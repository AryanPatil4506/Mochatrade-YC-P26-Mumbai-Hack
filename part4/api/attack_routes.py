from __future__ import annotations

"""api/attack_routes.py — Attack Simulation Lab API Endpoints

Exposes REST endpoints for the Attack Simulation Lab as specified in PART4.md:
  GET  /part4/attacks
  GET  /part4/attacks/{scenario}
  POST /part4/attacks/{scenario}/generate
  POST /part4/attacks/{scenario}/run

Attacks do NOT directly execute any tool. They generate a standard Proposed Action Object
that must go through the normal Part 2 -> Part 3 -> Part 4 pipeline.
"""

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from attacks.simulator import AttackSimulator, default_simulator
from executor.model import ProposedAction

attack_router = APIRouter(prefix="/part4/attacks", tags=["Attack Simulation Lab"])


class ScenarioRunRequest(BaseModel):
    request_id: Optional[str] = Field(default=None, description="Optional custom request ID")
    agent_id: Optional[str] = Field(default=None, description="Optional custom agent ID")
    session_id: Optional[str] = Field(default=None, description="Optional custom session ID")
    destination: Optional[str] = Field(default=None, description="Optional custom destination")
    query: Optional[str] = Field(default=None, description="Optional custom SQL query")
    target_resource: Optional[str] = Field(default=None, description="Optional custom target resource")
    custom_prompt: Optional[str] = Field(default=None, description="Optional custom untrusted injection prompt")
    extra_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context fields")


def get_simulator() -> AttackSimulator:
    return default_simulator


def set_pipeline_runner(runner) -> None:
    """Register the pipeline runner function (Part 2 -> Part 3 -> Part 4)."""
    default_simulator.set_pipeline_runner(runner)


@attack_router.get("", response_model=List[Dict[str, Any]], summary="List attack scenarios")
@attack_router.get("/", response_model=List[Dict[str, Any]], include_in_schema=False)
def list_attack_scenarios() -> List[Dict[str, Any]]:
    """Return all available attack scenarios with their metadata."""
    return default_simulator.list_scenarios()


@attack_router.get("/{scenario}", response_model=Dict[str, Any], summary="Get scenario details")
def get_attack_scenario(scenario: str) -> Dict[str, Any]:
    """Retrieve details and expected behavior for a given attack scenario."""
    meta = default_simulator.get_scenario(scenario)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario}' not found. Supported scenarios: {list(default_simulator.get_scenario(s)['id'] for s in ['prompt_injection', 'privilege_abuse', 'destructive_sql', 'data_exfiltration'] if default_simulator.get_scenario(s))}",
        )
    return meta


@attack_router.post("/{scenario}/generate", summary="Generate a Proposed Action Object")
def generate_attack_scenario(
    scenario: str,
    payload: Optional[ScenarioRunRequest] = None,
) -> Dict[str, Any]:
    """Generate a standard Proposed Action Object for testing/demonstration without executing."""
    meta = default_simulator.get_scenario(scenario)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario}' not found.",
        )

    overrides = payload.model_dump(exclude_unset=True) if payload else {}
    action: ProposedAction = default_simulator.generate_action(scenario, **overrides)
    return {
        "scenario": scenario,
        "proposed_action": asdict(action),
    }


@attack_router.post("/{scenario}/run", summary="Run attack simulation through pipeline")
def run_attack_scenario(
    scenario: str,
    payload: Optional[ScenarioRunRequest] = None,
) -> Dict[str, Any]:
    """Dispatch an attack scenario through the security pipeline.

    CRITICAL: Does NOT directly execute any tool. If a pipeline runner is configured,
    the action is sent through Part 2 -> Part 3 -> Part 4. Otherwise, returns the
    generated action ready for upstream pipeline ingestion.
    """
    meta = default_simulator.get_scenario(scenario)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario}' not found.",
        )

    overrides = payload.model_dump(exclude_unset=True) if payload else {}
    result = default_simulator.run_simulation(scenario, **overrides)
    return result
