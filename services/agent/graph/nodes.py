"""The seven LangGraph nodes for one agent turn.

1. receive_input     — record the user's message
2. gather_context    — read any external sources needed, via ContextAdapter (taints them)
3. plan_action       — non-authoritative LLM call proposes a tool call
4. build_proposal    — assemble the frozen ProposedAction (server fields + taint ledger)
5. gateway_call      — POST to the gateway; fail closed on any error/timeout
6. handle_decision   — branch on ALLOW / REQUIRE_APPROVAL / BLOCK
7. respond           — produce the final assistant-facing message

Tool execution in `handle_decision` is a STUB for this scope (Part 4 /
executor is a teammate's build): on ALLOW it only logs
"would execute: <tool>.<operation>" instead of calling a real executor.
Second-order taint: whatever that stub "result" says is re-tainted through
the same ContextAdapter before anything downstream could see it, per
CLAUDE.md's "tool results are untrusted too".
"""

from __future__ import annotations

import os

import httpx

from packages.contracts.enums import TaintSource
from packages.contracts.schemas import Decision, ProposedAction
from services.agent import events
from services.agent.context.adapter import ContextAdapter
from services.agent.context.taint import TaintLedger
from services.agent.graph.state import AgentState
from services.agent.llm.client import propose_tool_call
from services.agent.proposal.builder import build_proposed_action

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8002")
GATEWAY_TIMEOUT_SECONDS = 5.0


async def receive_input(state: AgentState) -> dict:
    transcript = list(state.get("transcript", []))
    transcript.append({"role": "user", "content": state["user_request"]})
    await events.publish(state["session_id"], {"type": "user_message", "content": state["user_request"]})
    return {"transcript": transcript, "step": 0}


async def gather_context(state: AgentState) -> dict:
    """Look up any external sources the request seems to reference.

    Deliberately simple keyword routing for this scaffold — a real
    retrieval step would live here without changing the taint contract:
    every read still goes through `adapter.read`.
    """

    ledger: TaintLedger = state["ledger"]
    adapter: ContextAdapter = state["adapter"]
    step = state.get("step", 0) + 1

    lowered = state["user_request"].lower()
    observed: list[str] = []

    import re

    ticket_match = re.search(r"ticket #?(\d+)", lowered)
    if ticket_match:
        content = adapter.read(TaintSource.TICKET, ticket_match.group(1), step)
        observed.append(f"ticket #{ticket_match.group(1)}: {content}")

    contact_match = re.search(r"customer (\d+)", lowered)
    if contact_match:
        content = adapter.read(TaintSource.DATABASE_RECORD, f"cust-{contact_match.group(1)}", step)
        observed.append(f"customer {contact_match.group(1)}: {content}")

    for entry in ledger.since_step(step):
        await events.publish(
            state["session_id"],
            {"type": "taint_read", "source": entry.source.value, "reference": entry.reference},
        )

    return {"step": step, "observed_context": observed}


async def plan_action(state: AgentState) -> dict:
    proposal = propose_tool_call(state["user_request"], state.get("observed_context", []))
    await events.publish(
        state["session_id"],
        {"type": "plan", "function_name": proposal.function_name, "arguments": proposal.arguments},
    )
    return {"tool_proposal": proposal}


async def build_proposal(state: AgentState) -> dict:
    action: ProposedAction = build_proposed_action(
        agent_id=state["agent_id"],
        session_id=state["session_id"],
        user_request=state["user_request"],
        proposal=state["tool_proposal"],
        ledger=state["ledger"],
    )
    await events.publish(
        state["session_id"],
        {
            "type": "proposed_action",
            "request_id": str(action.request_id),
            "tool_name": action.tool_name.value,
            "operation": action.operation.value,
        },
    )
    return {"proposed_action": action}


async def gateway_call(state: AgentState) -> dict:
    action: ProposedAction = state["proposed_action"]
    try:
        async with httpx.AsyncClient(timeout=GATEWAY_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{GATEWAY_URL}/v1/gateway/evaluate",
                content=action.model_dump_json(),
                headers={"content-type": "application/json"},
            )
            response.raise_for_status()
            decision = Decision.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        decision = Decision.fail_closed(action.request_id)

    await events.publish(
        state["session_id"],
        {
            "type": "decision",
            "request_id": str(decision.request_id),
            "decision": decision.decision.value,
            "risk_score": decision.risk_score,
        },
    )
    return {"decision": decision}


async def handle_decision(state: AgentState) -> dict:
    decision: Decision = state["decision"]
    action: ProposedAction = state["proposed_action"]
    ledger: TaintLedger = state["ledger"]
    adapter: ContextAdapter = state["adapter"]
    step = state.get("step", 0) + 1

    if decision.decision.value == "ALLOW":
        # TEMPORARY STUB — no real executor call in this scope (Part 4).
        # Logs intent only; never actually performs the tool operation.
        stub_result = f"would execute: {action.tool_name.value}.{action.operation.value}"
        print(f"[executor-stub] {stub_result}")

        # Tool results are untrusted too — re-taint via the same adapter so
        # second-order injection (a poisoned tool result) is covered.
        adapter.read(TaintSource.DATABASE_RECORD, f"tool-result:{action.request_id}", step, content=stub_result)
        tool_result = stub_result
    elif decision.decision.value == "REQUIRE_APPROVAL":
        tool_result = "pending human approval"
    else:
        tool_result = None

    await events.publish(state["session_id"], {"type": "tool_result", "result": tool_result})
    return {"step": step, "tool_result": tool_result}


async def respond(state: AgentState) -> dict:
    decision: Decision = state["decision"]
    outcome = decision.decision.value

    if outcome == "ALLOW":
        message = f"Done - {state.get('tool_result')}."
    elif outcome == "REQUIRE_APPROVAL":
        message = "This action needs human approval before it can proceed."
    else:
        message = "This action requires authorization you do not hold."

    transcript = list(state.get("transcript", []))
    transcript.append({"role": "assistant", "content": message})
    await events.publish(state["session_id"], {"type": "assistant_message", "content": message})
    await events.publish(state["session_id"], {"type": "turn_complete"})

    return {"transcript": transcript, "final_response": message}
