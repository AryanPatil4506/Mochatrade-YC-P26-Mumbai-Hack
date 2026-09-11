"""Contract round-trip and validation tests (packages/contracts)."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.contracts.schemas import Decision, ProposedAction, RiskFactors

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_NAMES = ["benign_action", "injected_action", "privilege_abuse_action"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_round_trips(name):
    data = json.loads((FIXTURES_DIR / f"{name}.json").read_text())
    action = ProposedAction.model_validate(data)
    assert ProposedAction.model_validate_json(action.model_dump_json()) == action


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_rejects_unknown_field(name):
    data = json.loads((FIXTURES_DIR / f"{name}.json").read_text())
    data["unexpected_field"] = "nope"
    with pytest.raises(ValidationError):
        ProposedAction.model_validate(data)


def test_risk_factors_reject_out_of_range():
    base = dict(
        tool_sensitivity=0, data_sensitivity=0, privilege_level=0, destination_risk=0,
        reversibility=0, injection_signal=0, behavioral_anomaly=0,
    )
    for key in base:
        with pytest.raises(ValidationError):
            RiskFactors(**{**base, key: 101})
        with pytest.raises(ValidationError):
            RiskFactors(**{**base, key: -1})


def test_proposed_action_rejects_bad_enum():
    data = json.loads((FIXTURES_DIR / "benign_action.json").read_text())
    data["tool_name"] = "carrier_pigeon"
    with pytest.raises(ValidationError):
        ProposedAction.model_validate(data)


def test_decision_requires_human_approval_is_derived():
    factors = RiskFactors(
        tool_sensitivity=0, data_sensitivity=0, privilege_level=0, destination_risk=0,
        reversibility=0, injection_signal=0, behavioral_anomaly=0,
    )
    from datetime import datetime, timezone

    d = Decision(
        request_id=uuid4(), decision="REQUIRE_APPROVAL", risk_score=65, risk_factors=factors,
        policy_rule_triggered="anomalous_sensitive_action", timestamp=datetime.now(timezone.utc), audit_log_id=uuid4(),
    )
    assert d.requires_human_approval is True

    d_allow = Decision(
        request_id=uuid4(), decision="ALLOW", risk_score=9, risk_factors=factors,
        timestamp=datetime.now(timezone.utc), audit_log_id=uuid4(),
    )
    assert d_allow.requires_human_approval is False

    # The field can't be set independently of `decision` — even an
    # adversarial/buggy caller passing the wrong value gets overwritten.
    d_lied = Decision(
        request_id=uuid4(), decision="ALLOW", risk_score=9, risk_factors=factors,
        requires_human_approval=True, timestamp=datetime.now(timezone.utc), audit_log_id=uuid4(),
    )
    assert d_lied.requires_human_approval is False

    # And it survives a full JSON round trip (the real gateway -> agent path).
    d_roundtrip = Decision.model_validate_json(d.model_dump_json())
    assert d_roundtrip == d


def test_decision_fail_closed_shape():
    d = Decision.fail_closed(uuid4())
    assert d.decision.value == "BLOCK"
    assert d.risk_score == 100
    assert d.policy_rule_triggered == "gateway_unavailable"
    assert d.capability_token is None
    assert d.requires_human_approval is False
