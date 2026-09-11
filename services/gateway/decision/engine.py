"""The real Part 3 decision engine.

This promotes the threshold/composer logic that used to live inline in
services/gateway/api.py (labeled TEMPORARY because capability tokens, the
approval workflow, and audit logging were out of scope for that session) into
its permanent home, and fills in the three pieces that were previously
faked:

- capability_token is now a real HMAC-signed, single-use token (capability.py)
- REQUIRE_APPROVAL decisions now create a real, persisted approval record
- every decision opens a real audit_log row (executed=False until the
  executor actually runs a tool)

The scoring/threshold math itself (composer.py's weights+floors, and the
4-band lookup below) is unchanged — it already matches the five canonical
test scenarios exactly, so it was kept rather than replaced by a
teammate's separate rule-engine implementation (see integration notes).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import yaml

from packages.contracts.enums import DecisionValue
from packages.contracts.schemas import Decision, ProposedAction, RiskAssessment
from services.executor.audit import logger as audit_logger
from services.gateway.approvals.queue import create_pending_approval
from services.gateway.decision.capability import issue_token
from services.gateway.decision.events import publish_decision
from services.gateway.detection.orchestrator import run_detectors

logger = logging.getLogger(__name__)

_THRESHOLDS_PATH = Path(__file__).resolve().parents[3] / "config" / "thresholds.yaml"
BANDS = yaml.safe_load(_THRESHOLDS_PATH.read_text())["bands"]

# Idempotency cache: duplicate request_id returns the cached Decision,
# detectors not re-run (frozen contract requirement).
_decision_cache: dict[UUID, Decision] = {}


def _apply_threshold_bands(risk_score: int, escalation_floor_triggered: str | None) -> tuple[DecisionValue, str | None]:
    for band in BANDS:
        if band["min"] <= risk_score < band["max"]:
            decision = DecisionValue(band["decision"])
            rule = escalation_floor_triggered
            if band["set_policy_rule"] and rule is None:
                rule = f"elevated_risk_score_{risk_score}"
            return decision, rule
    return DecisionValue.BLOCK, escalation_floor_triggered  # score == 100 edge case


def _decision_from_assessment(action: ProposedAction, assessment: RiskAssessment) -> Decision:
    decision_value, policy_rule = _apply_threshold_bands(assessment.risk_score, assessment.escalation_floor_triggered)

    capability_token = None
    if decision_value == DecisionValue.ALLOW:
        capability_token = issue_token(
            request_id=action.request_id,
            decision="ALLOW",
            tool_name=action.tool_name.value,
            operation=action.operation.value,
            arguments=action.arguments,
            target_resource=action.target_resource,
        )

    decision = Decision(
        request_id=action.request_id,
        decision=decision_value,
        risk_score=assessment.risk_score,
        risk_factors=assessment.risk_factors,
        policy_rule_triggered=policy_rule,
        explanation=None,  # async LLM explainer is out of scope; dashboard shows a template
        capability_token=capability_token,
        timestamp=datetime.now(timezone.utc),
        audit_log_id=uuid4(),
    )

    audit_logger.create_log(action=action, decision=decision, executed=False)

    if decision_value == DecisionValue.REQUIRE_APPROVAL:
        create_pending_approval(action=action, decision=decision)

    return decision


async def evaluate(action: ProposedAction) -> Decision:
    cached = _decision_cache.get(action.request_id)
    if cached is not None:
        return cached

    try:
        assessment = await run_detectors(action)
        decision = _decision_from_assessment(action, assessment)
    except Exception:
        logger.exception("gateway evaluate failed for request_id=%s", action.request_id)
        decision = Decision.fail_closed(action.request_id)
        audit_logger.create_log(action=action, decision=decision, executed=False)

    _decision_cache[action.request_id] = decision
    await publish_decision(action, decision)
    return decision
