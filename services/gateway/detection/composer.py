"""Weights + escalation floors — composes the seven risk factors into a
single `risk_score`. See CLAUDE.md — "Composite Score & Decision".

This module produces `RiskAssessment.risk_score` /
`risk_factors` / `escalation_floor_triggered` (Part 2's output contract). It
does NOT decide ALLOW/REQUIRE_APPROVAL/BLOCK — that's Part 3's threshold
bands in `services/gateway/decision/`, out of scope here.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

from packages.contracts.schemas import RiskFactors

_WEIGHTS_PATH = Path(__file__).resolve().parents[3] / "config" / "weights.yaml"


def _load_weights() -> dict[str, float]:
    weights = yaml.safe_load(_WEIGHTS_PATH.read_text())
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-9, f"weights must sum to 1.0, got {total}"
    return weights


WEIGHTS = _load_weights()

# (floor, rule_name, predicate) — checked highest floor first so that when
# multiple conditions trigger, the strongest one wins deterministically.
_FLOOR_RULES: list[tuple[int, str, "callable"]] = [
    (90, "privilege_never_granted", lambda f: f.privilege_level == 100),
    (85, "confirmed_injection", lambda f: f.injection_signal >= 85),
    (
        80,
        "suspected_injection_exfiltration",
        lambda f: f.injection_signal >= 60 and f.destination_risk >= 60,
    ),
    (
        70,
        "sensitive_data_irreversible_egress",
        lambda f: f.data_sensitivity >= 70 and f.destination_risk >= 60 and f.reversibility >= 80,
    ),
    (
        65,
        "anomalous_sensitive_action",
        lambda f: f.behavioral_anomaly >= 85 and f.data_sensitivity >= 70,
    ),
    (
        62,
        "high_impact_irreversible_op",
        lambda f: f.reversibility >= 90 and f.tool_sensitivity >= 80,
    ),
]


def highest_floor(f: RiskFactors) -> tuple[int, str | None]:
    for floor, rule, predicate in _FLOOR_RULES:
        if predicate(f):
            return floor, rule
    return 0, None


def compose(f: RiskFactors) -> tuple[int, str | None]:
    weighted = sum(WEIGHTS[k] * getattr(f, k) for k in WEIGHTS)
    floor, rule = highest_floor(f)
    weighted_rounded = int(Decimal(str(weighted)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    score = max(weighted_rounded, floor)
    return min(score, 100), rule
