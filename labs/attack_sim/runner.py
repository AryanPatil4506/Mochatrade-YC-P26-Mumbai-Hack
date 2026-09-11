"""Attack Simulation Lab runner.

Generates a scenario's ProposedAction and sends it through the *real*
pipeline exactly as a real agent would: POST to the gateway's
/v1/gateway/evaluate, and only if that returns an ALLOW capability_token,
POST to the executor's own /v1/execute with it. The runner never calls a
tool function directly — CLAUDE.md's core principle for the lab.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from labs.attack_sim.scenarios.generators import SCENARIOS, SCENARIOS_METADATA

_GATEWAY_BASE_URL = os.environ.get("SENTINEL_GATEWAY_URL", "http://localhost:8002")
_EXECUTOR_BASE_URL = os.environ.get("SENTINEL_EXECUTOR_URL", "http://localhost:8003")


def list_scenarios() -> list[dict]:
    return list(SCENARIOS_METADATA.values())


async def run_scenario(scenario_id: str, **overrides: Any) -> dict:
    generator = SCENARIOS.get(scenario_id)
    if generator is None:
        raise ValueError(f"Unknown attack scenario '{scenario_id}'. Supported: {', '.join(sorted(SCENARIOS))}")

    action = generator(**overrides)
    action_json = action.model_dump(mode="json")

    async with httpx.AsyncClient(timeout=10.0) as client:
        eval_resp = await client.post(f"{_GATEWAY_BASE_URL}/v1/gateway/evaluate", json=action_json)
        eval_resp.raise_for_status()
        decision = eval_resp.json()

        execution: Optional[dict] = None
        if decision.get("capability_token"):
            exec_resp = await client.post(
                f"{_EXECUTOR_BASE_URL}/v1/execute",
                json=action_json,
                headers={"X-Capability-Token": decision["capability_token"]},
            )
            execution = exec_resp.json() if exec_resp.headers.get("content-type", "").startswith("application/json") else None

    return {
        "scenario": scenario_id,
        "proposed_action": action_json,
        "decision": decision,
        "execution": execution,
        "executed": bool(execution and execution.get("executed")),
    }
