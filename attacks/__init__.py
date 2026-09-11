from __future__ import annotations

"""attacks package — Sentinel AI Attack Simulation Lab."""

from attacks.payload import (
    DATA_EXFILTRATION_BODY,
    DATA_EXFILTRATION_DESTINATION,
    DATA_EXFILTRATION_SUBJECT,
    DATA_EXFILTRATION_TARGET_RESOURCE,
    DESTRUCTIVE_SQL_PAYLOAD,
    DESTRUCTIVE_SQL_TARGET_RESOURCE,
    PRIVILEGE_ABUSE_AGENT_ID,
    PRIVILEGE_ABUSE_AGENT_ROLE,
    PRIVILEGE_ABUSE_QUERY,
    PRIVILEGE_ABUSE_TARGET_RESOURCE,
    PROMPT_INJECTION_DESTINATION,
    PROMPT_INJECTION_PAYLOAD,
    PROMPT_INJECTION_TARGET_RESOURCE,
)
from attacks.scenarios import (
    ATTACK_SCENARIOS,
    SCENARIOS_METADATA,
    generate_data_exfiltration,
    generate_destructive_sql,
    generate_privilege_abuse,
    generate_prompt_injection,
)
from attacks.simulator import AttackSimulator, default_simulator

__all__ = [
    "AttackSimulator",
    "default_simulator",
    "ATTACK_SCENARIOS",
    "SCENARIOS_METADATA",
    "generate_prompt_injection",
    "generate_privilege_abuse",
    "generate_destructive_sql",
    "generate_data_exfiltration",
    "PROMPT_INJECTION_PAYLOAD",
    "PROMPT_INJECTION_DESTINATION",
    "PROMPT_INJECTION_TARGET_RESOURCE",
    "PRIVILEGE_ABUSE_AGENT_ROLE",
    "PRIVILEGE_ABUSE_AGENT_ID",
    "PRIVILEGE_ABUSE_QUERY",
    "PRIVILEGE_ABUSE_TARGET_RESOURCE",
    "DESTRUCTIVE_SQL_PAYLOAD",
    "DESTRUCTIVE_SQL_TARGET_RESOURCE",
    "DATA_EXFILTRATION_DESTINATION",
    "DATA_EXFILTRATION_TARGET_RESOURCE",
    "DATA_EXFILTRATION_SUBJECT",
    "DATA_EXFILTRATION_BODY",
]
