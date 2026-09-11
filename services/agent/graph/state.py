"""LangGraph state for one agent turn.

Plain TypedDict — each node returns a partial dict that LangGraph merges
into the running state. `ledger` and `adapter` are session-scoped objects
threaded through by reference (not replaced by nodes), everything else is
turn-scoped data.
"""

from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID

from packages.contracts.schemas import Decision, ProposedAction
from services.agent.context.adapter import ContextAdapter
from services.agent.context.taint import TaintLedger
from services.agent.llm.client import ToolCallProposal


class AgentState(TypedDict, total=False):
    agent_id: str
    session_id: UUID
    user_request: str
    step: int
    transcript: list[dict[str, Any]]

    ledger: TaintLedger
    adapter: ContextAdapter
    observed_context: list[str]

    tool_proposal: ToolCallProposal
    proposed_action: ProposedAction
    decision: Decision

    tool_result: str | None
    final_response: str
