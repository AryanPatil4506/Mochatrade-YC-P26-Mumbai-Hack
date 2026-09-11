"""Best-effort bridge from the gateway process to the executor's shared
`/v1/events` SSE hub — the single GET /v1/events SSE endpoint all services
publish to. Since the gateway and executor are separate
processes/ports, "publish" means one small internal HTTP POST — never a
network call to decide anything, purely fire-and-forget telemetry for the
dashboard's IncidentTimeline/RiskGauge. If the executor is down or slow this
must never block or fail an /v1/gateway/evaluate call.
"""

from __future__ import annotations

import logging
import os

import httpx

from packages.contracts.schemas import Decision, ProposedAction

logger = logging.getLogger(__name__)

_EXECUTOR_BASE_URL = os.environ.get("SENTINEL_EXECUTOR_URL", "http://localhost:8003")
_TIMEOUT_SECONDS = 0.5


async def publish_decision(action: ProposedAction, decision: Decision) -> None:
    event = {
        "type": "decision",
        "request_id": str(decision.request_id),
        "agent_id": action.agent_id,
        "tool_name": action.tool_name.value,
        "operation": action.operation.value,
        "decision": decision.decision.value,
        "risk_score": decision.risk_score,
        "policy_rule_triggered": decision.policy_rule_triggered,
        "timestamp": decision.timestamp.isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            await client.post(f"{_EXECUTOR_BASE_URL}/internal/events", json=event)
    except httpx.HTTPError:
        logger.debug("event publish to executor failed (non-fatal)", exc_info=True)
