"""Agent service (Part 1), :8001.

POST /v1/agent/sessions              create a session
POST /v1/agent/messages              202, runs the graph, streams over SSE
GET  /v1/agent/sessions/{id}         transcript + taint ledger
GET  /v1/agent/sessions/{id}/events  SSE stream for that session
POST /v1/agent/simulate-compromise   calls the executor directly, no token
                                      (stubbed here — real executor is Part 4)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from services.agent import events
from services.agent.context.adapter import ContextAdapter
from services.agent.context.taint import TaintLedger
from services.agent.graph.build import get_agent_graph

_EXECUTOR_BASE_URL = os.environ.get("SENTINEL_EXECUTOR_URL", "http://localhost:8003")

app = FastAPI(title="Sentinel Agent Service")

_sessions: dict[UUID, dict[str, Any]] = {}


class CreateSessionRequest(BaseModel):
    agent_id: str


class CreateSessionResponse(BaseModel):
    session_id: UUID
    agent_id: str


class SendMessageRequest(BaseModel):
    session_id: UUID
    user_request: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "agent"}


@app.post("/v1/agent/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    session_id = uuid4()
    ledger = TaintLedger()
    _sessions[session_id] = {
        "agent_id": req.agent_id,
        "ledger": ledger,
        "adapter": ContextAdapter(ledger),
        "transcript": [],
    }
    return CreateSessionResponse(session_id=session_id, agent_id=req.agent_id)


@app.post("/v1/agent/messages", status_code=202)
async def send_message(req: SendMessageRequest) -> dict:
    session = _sessions.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session_id")

    graph = get_agent_graph()
    initial_state = {
        "agent_id": session["agent_id"],
        "session_id": req.session_id,
        "user_request": req.user_request,
        "transcript": session["transcript"],
        "ledger": session["ledger"],
        "adapter": session["adapter"],
        "observed_context": [],
    }

    async def run() -> None:
        final_state = await graph.ainvoke(initial_state)
        session["transcript"] = final_state.get("transcript", [])

    import asyncio

    asyncio.create_task(run())
    return {"accepted": True, "session_id": str(req.session_id)}


@app.get("/v1/agent/sessions/{session_id}")
async def get_session(session_id: UUID) -> dict:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session_id")

    ledger: TaintLedger = session["ledger"]
    return {
        "session_id": str(session_id),
        "agent_id": session["agent_id"],
        "transcript": session["transcript"],
        "taint_ledger": [
            {
                "entry_id": str(e.entry_id),
                "source": e.source.value,
                "reference": e.reference,
                "content": e.content,
                "read_at": e.read_at.isoformat(),
                "step": e.step,
            }
            for e in ledger.all()
        ],
    }


@app.get("/v1/agent/sessions/{session_id}/events")
async def stream_events(session_id: UUID) -> EventSourceResponse:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="unknown session_id")

    async def event_generator():
        async for event in events.subscribe(session_id):
            yield {"event": event.get("type", "message"), "data": event}

    return EventSourceResponse(event_generator())


@app.post("/v1/agent/simulate-compromise")
async def simulate_compromise() -> dict:
    """For the compromised-agent test: calls the executor's /v1/execute
    directly with no capability token, exactly as a compromised agent trying
    to bypass the gateway would. Demonstrates layer 3 of the Enforcement
    Boundary (capability tokens) rejecting an action that never went through
    /v1/gateway/evaluate at all."""

    fake_action = {
        "request_id": str(uuid4()),
        "agent_id": "compromised-agent",
        "session_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": "database",
        "operation": "delete",
        "arguments": {"query": "DROP TABLE customers;"},
        "target_resource": "customers",
        "destination": None,
        "context": {"user_request": "n/a", "untrusted_content_sources": []},
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{_EXECUTOR_BASE_URL}/v1/execute",
                json=fake_action,
                headers={"X-Capability-Token": "forged-token-no-signature"},
            )
    except httpx.HTTPError as exc:
        return {"outcome": "executor_unreachable", "message": str(exc)}

    return {
        "outcome": "denied" if resp.status_code == 403 else "unexpected",
        "status_code": resp.status_code,
        "executor_response": resp.json(),
    }
