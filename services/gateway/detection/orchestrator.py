"""Runs all seven Part 2 detectors concurrently and composes a RiskAssessment.

Per CLAUDE.md, all seven detectors are pure functions run concurrently via
`asyncio.gather` (budget: p95 under 400ms with classifiers warm). Six of the
seven are cheap synchronous pure functions; only `injection.detect_injection`
has real async I/O (the optional classifier call). All seven are still
dispatched through one `asyncio.gather` — the synchronous ones via
`asyncio.to_thread` — so this module's shape matches the spec even though
today's synchronous detectors would be just as fast called inline.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from packages.contracts.schemas import ProposedAction, RiskAssessment, RiskEvidence, RiskFactors
from services.gateway.detection.behavior import compute_behavioral_anomaly, record_outcome
from services.gateway.detection.composer import compose
from services.gateway.detection.data_classifier import compute_data_sensitivity
from services.gateway.detection.destination import classify_destination
from services.gateway.detection.injection import detect_injection
from services.gateway.detection.privilege import compute_privilege
from services.gateway.detection.reversibility import compute_reversibility
from services.gateway.detection.tool_sensitivity import compute_tool_sensitivity

ENGINE_VERSION = "0.1.0"

_ID_LIKE_KEYS = {"id", "contact_id", "ticket_id", "record_id"}


def estimate_record_count(action: ProposedAction) -> int:
    for key in ("record_count", "count", "limit"):
        value = action.arguments.get(key)
        if isinstance(value, int):
            return value
    return 1


def is_unscoped(action: ProposedAction) -> bool:
    args = action.arguments
    if any(k in args for k in _ID_LIKE_KEYS):
        return False
    if args.get("filter") or args.get("where"):
        return False
    return True


async def run_detectors(action: ProposedAction) -> RiskAssessment:
    untrusted_texts = [s.content for s in action.context.untrusted_content_sources]
    record_count = estimate_record_count(action)
    unscoped = is_unscoped(action)

    (
        tool_sens,
        data_result,
        priv,
        dest,
        rev,
        behavior_result,
        injection_result,
    ) = await asyncio.gather(
        asyncio.to_thread(
            compute_tool_sensitivity, action.tool_name.value, action.operation.value, action.target_resource, unscoped
        ),
        asyncio.to_thread(
            compute_data_sensitivity,
            untrusted_texts + [json.dumps(action.arguments), action.target_resource],
            record_count,
        ),
        asyncio.to_thread(
            compute_privilege, action.agent_id, action.tool_name.value, action.operation.value, record_count, action.destination
        ),
        asyncio.to_thread(classify_destination, action.destination, action.context.user_request),
        asyncio.to_thread(compute_reversibility, action.operation.value, action.target_resource, action.arguments),
        asyncio.to_thread(
            compute_behavioral_anomaly,
            session_id=action.session_id,
            timestamp=action.timestamp,
            user_request=action.context.user_request,
            operation=action.operation.value,
            tool_name=action.tool_name.value,
            target_resource=action.target_resource,
            destination=action.destination,
            record_count=record_count,
        ),
        detect_injection(untrusted_texts),
    )

    factors = RiskFactors(
        tool_sensitivity=tool_sens,
        data_sensitivity=data_result.score,
        privilege_level=priv,
        destination_risk=dest,
        reversibility=rev,
        injection_signal=injection_result.score,
        behavioral_anomaly=behavior_result.score,
    )

    score, rule = compose(factors)
    record_outcome(action.session_id, score)

    evidence = RiskEvidence(
        injection_families=injection_result.families,
        detected_entity_types=data_result.detected_entity_types,
        record_count_estimate=record_count,
        intent_drift=behavior_result.intent_drift,
        detector_mode=injection_result.detector_mode,
    )

    return RiskAssessment(
        request_id=action.request_id,
        risk_factors=factors,
        risk_score=score,
        escalation_floor_triggered=rule,
        evidence=evidence,
        computed_at=datetime.now(timezone.utc),
        engine_version=ENGINE_VERSION,
    )
