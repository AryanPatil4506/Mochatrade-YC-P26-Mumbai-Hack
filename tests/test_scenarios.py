"""The five canonical scenarios — must match exactly.

Also: determinism (10x identical input -> byte-identical output),
monotonicity (raising any one factor never lowers risk_score), and
boundary tests at exactly 29/30/59/60/79/80.
"""

from __future__ import annotations

import pytest

from packages.contracts.schemas import RiskFactors
from services.gateway.detection.composer import compose

FACTOR_NAMES = (
    "tool_sensitivity",
    "data_sensitivity",
    "privilege_level",
    "destination_risk",
    "reversibility",
    "injection_signal",
    "behavioral_anomaly",
)

SCENARIOS = {
    "5.1_benign_crm_read": (
        dict(
            tool_sensitivity=30, data_sensitivity=20, privilege_level=0, destination_risk=0,
            reversibility=5, injection_signal=0, behavioral_anomaly=5,
        ),
        9, None,
    ),
    "5.2_poisoned_ticket_exfil_email": (
        dict(
            tool_sensitivity=80, data_sensitivity=90, privilege_level=60, destination_risk=95,
            reversibility=95, injection_signal=95, behavioral_anomaly=85,
        ),
        86, "confirmed_injection",
    ),
    "5.3_user_requested_risky_export": (
        dict(
            tool_sensitivity=80, data_sensitivity=90, privilege_level=60, destination_risk=80,
            reversibility=95, injection_signal=0, behavioral_anomaly=25,
        ),
        70, "sensitive_data_irreversible_egress",
    ),
    "5.4_privilege_abuse_prod_delete": (
        dict(
            tool_sensitivity=100, data_sensitivity=85, privilege_level=100, destination_risk=0,
            reversibility=100, injection_signal=0, behavioral_anomaly=70,
        ),
        90, "privilege_never_granted",
    ),
    "5.5_quiet_scope_creep": (
        dict(
            tool_sensitivity=55, data_sensitivity=85, privilege_level=70, destination_risk=0,
            reversibility=5, injection_signal=0, behavioral_anomaly=90,
        ),
        65, "anomalous_sensitive_action",
    ),
}


@pytest.mark.parametrize("name", SCENARIOS.keys())
def test_canonical_scenario(name):
    factors, expected_score, expected_rule = SCENARIOS[name]
    score, rule = compose(RiskFactors(**factors))
    assert (score, rule) == (expected_score, expected_rule)


def test_5_4_floor_overrides_weighted_sum():
    """The key regression test: weighted sum alone (60.5) would be an
    ordinary approval; the floor is what corrects it to BLOCK."""

    factors, _, _ = SCENARIOS["5.4_privilege_abuse_prod_delete"]
    f = RiskFactors(**factors)
    weighted = sum(compose.__globals__["WEIGHTS"][k] * getattr(f, k) for k in compose.__globals__["WEIGHTS"])
    assert weighted == pytest.approx(60.5)

    score, rule = compose(f)
    assert score == 90
    assert score > round(weighted)
    assert rule == "privilege_never_granted"


def test_determinism():
    factors, _, _ = SCENARIOS["5.2_poisoned_ticket_exfil_email"]
    f = RiskFactors(**factors)
    results = [compose(f) for _ in range(10)]
    assert len(set(results)) == 1


@pytest.mark.parametrize("factor_name", FACTOR_NAMES)
def test_monotonicity(factor_name):
    base = dict(
        tool_sensitivity=20, data_sensitivity=20, privilege_level=20, destination_risk=20,
        reversibility=20, injection_signal=20, behavioral_anomaly=20,
    )
    prev_score, _ = compose(RiskFactors(**base))
    for value in range(21, 101, 7):
        candidate = dict(base)
        candidate[factor_name] = value
        score, _ = compose(RiskFactors(**candidate))
        assert score >= prev_score
        prev_score = score


BOUNDARY_FACTORS: dict[int, dict[str, int]] = {
    29: dict(tool_sensitivity=0, data_sensitivity=0, privilege_level=0, destination_risk=45, reversibility=20, injection_signal=80, behavioral_anomaly=80),
    30: dict(tool_sensitivity=0, data_sensitivity=0, privilege_level=0, destination_risk=45, reversibility=30, injection_signal=80, behavioral_anomaly=80),
    59: dict(tool_sensitivity=0, data_sensitivity=60, privilege_level=80, destination_risk=45, reversibility=80, injection_signal=80, behavioral_anomaly=80),
    60: dict(tool_sensitivity=0, data_sensitivity=60, privilege_level=90, destination_risk=45, reversibility=80, injection_signal=80, behavioral_anomaly=80),
    79: dict(tool_sensitivity=70, data_sensitivity=100, privilege_level=90, destination_risk=45, reversibility=80, injection_signal=80, behavioral_anomaly=80),
    80: dict(tool_sensitivity=65, data_sensitivity=100, privilege_level=95, destination_risk=50, reversibility=80, injection_signal=80, behavioral_anomaly=80),
}


@pytest.mark.parametrize("target_score", [29, 30, 59, 60, 79, 80])
def test_composer_hits_exact_boundary_scores(target_score):
    """The composer must be able to land exactly on each decision-band
    boundary (29/30/59/60/79/80) with no floor overriding the weighted sum,
    so Part 3's half-open band comparisons (`30 <= s < 60`, etc.) are
    exercised at the exact edge rather than only approximately. Factor
    combinations below are deliberately chosen to stay clear of every
    escalation-floor predicate in composer.py.
    """

    f = RiskFactors(**BOUNDARY_FACTORS[target_score])
    score, rule = compose(f)
    assert rule is None
    assert score == target_score
