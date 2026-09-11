"""`tool_sensitivity` — static (tool, operation) lookup + additive modifiers."""

from __future__ import annotations

import re

_BASE_TABLE: dict[tuple[str, str], int] = {
    ("web", "read"): 20,
    ("web", "send"): 70,
    ("ticketing", "read"): 15,
    ("ticketing", "write"): 35,
    ("ticketing", "update"): 35,
    ("ticketing", "delete"): 70,
    ("crm", "read"): 30,
    ("crm", "write"): 55,
    ("crm", "update"): 55,
    ("crm", "delete"): 85,
    ("database", "read"): 45,
    ("database", "write"): 75,
    ("database", "update"): 75,
    ("database", "delete"): 95,
    ("email", "read"): 30,
    ("email", "delete"): 60,
    ("email", "send"): 80,
}

_PROD_TARGET = re.compile(r"^prod")


def compute_tool_sensitivity(tool_name: str, operation: str, target_resource: str, is_unscoped: bool) -> int:
    base = _BASE_TABLE.get((tool_name, operation), 0)
    score = base
    if _PROD_TARGET.match(target_resource or ""):
        score += 15
    if is_unscoped:
        score += 10
    return min(100, score)
