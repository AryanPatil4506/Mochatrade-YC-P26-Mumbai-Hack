"""GET /v1/policy — read-only view of the active weights/thresholds/floors."""

from __future__ import annotations

from services.gateway.decision.engine import BANDS
from services.gateway.detection.composer import _FLOOR_RULES, WEIGHTS


def get_policy_snapshot() -> dict:
    return {
        "weights": WEIGHTS,
        "thresholds": BANDS,
        "escalation_floors": [{"floor": f, "rule": r} for f, r, _ in _FLOOR_RULES],
    }
