"""Gateway service (Parts 2 + 3), :8002.

`POST /v1/gateway/evaluate` runs the real Part 2 pipeline (all seven
detectors + composer, see services/gateway/detection/) and the real Part 3
decision engine (services/gateway/decision/): threshold bands, HMAC-signed
capability tokens, approval-queue persistence, and audit logging. The
gateway never calls the executor directly (data flow is one-way, Part 1 ->
Part 2 -> Part 3 -> Part 4) — the agent calls the executor itself using the
capability_token this endpoint returns.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()  # picks up .env (signing keys, model overrides, etc.) before other imports

from fastapi import FastAPI

from packages.contracts.schemas import Decision, ProposedAction
from services.gateway.approvals.api import router as approvals_router
from services.gateway.decision import engine as decision_engine
from services.gateway.decision.policy import get_policy_snapshot

app = FastAPI(title="Sentinel Gateway Service (Parts 2 + 3)")
app.include_router(approvals_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "gateway"}


@app.post("/v1/gateway/evaluate", response_model=Decision)
async def evaluate(action: ProposedAction) -> Decision:
    return await decision_engine.evaluate(action)


@app.get("/v1/policy")
async def get_policy() -> dict:
    return get_policy_snapshot()
