"""Executor service (Part 4), :8003 — the enforcement point.

POST /v1/execute            header: X-Capability-Token -> ToolResult | 403
GET  /v1/audit/timeline?limit=50
GET  /v1/audit/{request_id}
POST /v1/lab/run/{scenario_id}
GET  /v1/events              SSE, shared event bus (see events.py)
POST /internal/events        gateway -> executor telemetry bridge, not part
                              of the frozen public contract

No tool implementations exist outside services/executor/tools/, and nothing
runs here without a capability token verified by verify.py first —
structural + capability-token enforcement layers per CLAUDE.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from packages.contracts.schemas import ProposedAction
from services.executor import events
from services.executor.audit import logger as audit_logger
from services.executor.tools.registry import get_tool
from services.gateway.decision.capability import TokenError
from services.executor.verify import verify_token
from labs.attack_sim.runner import list_scenarios, run_scenario

app = FastAPI(title="Sentinel Executor Service (Part 4)")


class ToolResult(BaseModel):
    request_id: UUID
    executed: bool
    success: bool
    tool_name: str
    operation: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "executor"}


@app.post("/v1/execute", response_model=ToolResult)
async def execute(action: ProposedAction, x_capability_token: str = Header(..., alias="X-Capability-Token")) -> ToolResult:
    try:
        verify_token(x_capability_token, action)
    except TokenError as exc:
        audit_logger.record_token_failure(action, reason=exc.reason)
        await events.publish({
            "type": "execution_denied",
            "request_id": str(action.request_id),
            "reason": exc.reason,
        })
        raise HTTPException(
            status_code=403,
            detail={"outcome": "denied", "message": "This action requires authorization you do not hold.", "reason": exc.reason},
        )

    tool_fn = get_tool(action.tool_name.value)
    if tool_fn is None:
        raise HTTPException(status_code=400, detail=f"unknown tool '{action.tool_name.value}'")

    result = tool_fn(
        operation=action.operation.value,
        arguments=action.arguments,
        target_resource=action.target_resource,
        destination=action.destination,
    )
    executed_at = datetime.now(timezone.utc).isoformat()
    success = bool(result.get("success")) if isinstance(result, dict) else False
    error = result.get("error") if isinstance(result, dict) else None

    audit_logger.mark_executed(action.request_id, executed=True, resolved_at=executed_at)
    audit_logger.record_execution(
        request_id=action.request_id,
        tool_name=action.tool_name.value,
        operation=action.operation.value,
        executed=True,
        success=success,
        result=result if isinstance(result, dict) else {"raw": result},
        error=error,
        executed_at=executed_at,
    )
    await events.publish({
        "type": "execution",
        "request_id": str(action.request_id),
        "tool_name": action.tool_name.value,
        "operation": action.operation.value,
        "success": success,
    })

    return ToolResult(
        request_id=action.request_id,
        executed=True,
        success=success,
        tool_name=action.tool_name.value,
        operation=action.operation.value,
        result=result if isinstance(result, dict) else {"raw": result},
        error=error,
        executed_at=executed_at,
    )


@app.get("/v1/audit/timeline")
async def audit_timeline(limit: int = 50) -> list[dict]:
    return [log.to_dict() for log in audit_logger.list_timeline(limit=limit)]


@app.get("/v1/audit/{request_id}")
async def audit_by_request(request_id: UUID) -> dict:
    log = audit_logger.get_by_request(request_id)
    if log is None:
        raise HTTPException(status_code=404, detail="no audit record for request_id")
    return log.to_dict()


@app.get("/v1/lab/scenarios")
async def lab_scenarios() -> list[dict]:
    return list_scenarios()


@app.post("/v1/lab/run/{scenario_id}")
async def lab_run(scenario_id: str, overrides: dict[str, Any] | None = None) -> dict:
    try:
        return await run_scenario(scenario_id, **(overrides or {}))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/internal/events")
async def internal_publish_event(event: dict[str, Any]) -> dict:
    """Gateway -> executor telemetry bridge. Not part of the frozen public
    API surface; exists only so the single shared /v1/events SSE hub can
    carry decision events from the other process."""

    await events.publish(event)
    return {"accepted": True}


@app.get("/v1/events")
async def stream_events() -> EventSourceResponse:
    async def event_generator():
        async for event in events.subscribe():
            # See the matching comment in services/agent/api.py: sse-starlette
            # would otherwise `str(dict)`-encode this (Python repr, not JSON).
            yield {"event": event.get("type", "message"), "data": json.dumps(event)}

    return EventSourceResponse(event_generator())
