"""`reversibility` — scored as irreversibility; higher means worse."""

from __future__ import annotations

import re

_BASE_MAP = {"read": 5, "write": 30, "update": 60, "send": 95}
_PROD_TARGET = re.compile(r"^prod")
_HARD_DELETE = re.compile(r"(?i)\b(drop table|truncate|hard delete|permanent(ly)? delete)\b")


def _looks_hard_delete(arguments: dict, target_resource: str) -> bool:
    haystack = " ".join(str(v) for v in arguments.values()) + " " + (target_resource or "")
    return bool(_HARD_DELETE.search(haystack))


def compute_reversibility(operation: str, target_resource: str, arguments: dict) -> int:
    if operation == "delete":
        base = 100 if _looks_hard_delete(arguments, target_resource) else 75
    else:
        base = _BASE_MAP.get(operation, 30)

    if _PROD_TARGET.match(target_resource or ""):
        base += 10

    return min(100, base)
