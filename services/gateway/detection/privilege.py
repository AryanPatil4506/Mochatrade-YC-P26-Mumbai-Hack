"""`privilege_level` — from config/agent_registry.yaml, per CLAUDE.md.

`100` always means "asked for something never granted" — the hardest
escalation floor keys off this value, so it must only ever be returned for
a true never-granted case (unknown tool, unknown operation).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "config" / "agent_registry.yaml"

_OPERATION_RANK = {"read": 0, "write": 1, "update": 1, "delete": 2, "send": 2}


def _load_registry() -> dict:
    raw = yaml.safe_load(_REGISTRY_PATH.read_text())
    return raw


_REGISTRY = _load_registry()


def get_agent_grant(agent_id: str) -> dict:
    return _REGISTRY.get("agents", {}).get(agent_id) or _REGISTRY["default"]


def compute_privilege(
    agent_id: str,
    tool_name: str,
    operation: str,
    record_count: int,
    destination: str | None,
) -> int:
    grant = get_agent_grant(agent_id)

    if tool_name not in grant["allowed_tools"]:
        return 100
    if operation not in grant["allowed_operations"]:
        return 100
    if record_count > grant["max_records_per_read"]:
        return 70

    pattern = grant.get("allowed_destinations_pattern")
    if destination:
        if not pattern or not re.match(pattern, destination):
            return 60

    current_rank = _OPERATION_RANK.get(operation, 0)
    max_allowed_rank = max((_OPERATION_RANK.get(op, 0) for op in grant["allowed_operations"]), default=0)
    if current_rank == max_allowed_rank:
        return 35
    return 5
