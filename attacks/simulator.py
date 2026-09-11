from __future__ import annotations

"""attacks/simulator.py — Attack Simulation Lab Engine

The Attack Simulation Lab generates realistic malicious ProposedAction objects
for testing and demonstration purposes.

CRITICAL SECURITY PRINCIPLE (PART4.md section 36):
  The Attack Simulator MUST NEVER directly execute any tool.
  All attacks must flow through the normal Part 2 -> Part 3 -> Part 4 pipeline:
    Attack Simulator -> Proposed Action -> Part 2 -> Part 3 -> Part 4 -> Enforce/Audit
"""

from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

from attacks.scenarios import (
    ATTACK_SCENARIOS,
    SCENARIOS_METADATA,
)
from executor.model import ProposedAction

# Type alias for a pipeline runner callback: receives ProposedAction, returns pipeline result
PipelineRunner = Callable[[ProposedAction], Any]


class AttackSimulator:
    """Attack Simulation Lab coordinator.

    Generates deterministic attack scenarios and dispatches them exclusively
    through an injected Part 2 -> Part 3 -> Part 4 pipeline runner.
    """

    def __init__(self, pipeline_runner: Optional[PipelineRunner] = None) -> None:
        self._pipeline_runner: Optional[PipelineRunner] = pipeline_runner

    def set_pipeline_runner(self, runner: PipelineRunner) -> None:
        """Register the pipeline runner (Part 2 -> Part 3 -> Part 4)."""
        self._pipeline_runner = runner

    @property
    def has_pipeline_runner(self) -> bool:
        return self._pipeline_runner is not None

    @staticmethod
    def list_scenarios() -> List[Dict[str, Any]]:
        """List all available attack scenarios with their metadata."""
        return list(SCENARIOS_METADATA.values())

    @staticmethod
    def get_scenario(scenario_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific scenario by identifier."""
        key = (scenario_name or "").strip().lower()
        return SCENARIOS_METADATA.get(key)

    @staticmethod
    def generate_action(scenario_name: str, **kwargs: Any) -> ProposedAction:
        """Generate a valid ProposedAction object for the given attack scenario.

        Does NOT execute any tool.
        """
        key = (scenario_name or "").strip().lower()
        generator = ATTACK_SCENARIOS.get(key)
        if not generator:
            supported = ", ".join(sorted(ATTACK_SCENARIOS.keys()))
            raise ValueError(
                f"Unknown attack scenario '{scenario_name}'. Supported scenarios: {supported}"
            )
        return generator(**kwargs)

    def run_simulation(
        self,
        scenario_name: str,
        pipeline_runner: Optional[PipelineRunner] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run an attack simulation.

        1. Generates the standard ProposedAction object.
        2. Dispatches it strictly through the pipeline runner if provided (or registered).
        3. Never calls any tool directly.
        """
        proposed_action = self.generate_action(scenario_name, **kwargs)
        action_dict = asdict(proposed_action)

        runner = pipeline_runner or self._pipeline_runner

        if runner is not None:
            # Send through the standard Part 2 -> Part 3 -> Part 4 pipeline
            pipeline_result = runner(proposed_action)
            return {
                "scenario": scenario_name,
                "status": "PIPELINE_EXECUTED",
                "message": "Attack simulation completed through Sentinel pipeline.",
                "proposed_action": action_dict,
                "pipeline_executed": True,
                "pipeline_result": pipeline_result,
            }

        # If no pipeline runner is registered yet, return the valid Proposed Action
        # ready for upstream ingestion, explicitly preventing direct tool execution.
        return {
            "scenario": scenario_name,
            "status": "PROPOSED_ACTION_GENERATED",
            "message": (
                "Proposed Action Object generated successfully. "
                "Per Part 4 specification, attacks must flow through Part 2 -> Part 3 -> Part 4. "
                "Direct tool execution is forbidden."
            ),
            "proposed_action": action_dict,
            "pipeline_executed": False,
            "pipeline_result": None,
        }


# Default singleton instance
default_simulator = AttackSimulator()
