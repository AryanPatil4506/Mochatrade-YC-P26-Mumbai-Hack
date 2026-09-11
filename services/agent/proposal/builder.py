"""Builds a ProposedAction from a model's ToolCallProposal.

Fills in every server-controlled field (`request_id`, `timestamp`,
`agent_id`) itself, derives `tool_name`/`operation` from the fixed mapping,
and pulls `context.untrusted_content_sources` from the taint ledger — never
from the model. `context.user_request` is copied verbatim, never rewritten.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from packages.contracts.schemas import ActionContext, ProposedAction, UntrustedContentSource
from services.agent.context.taint import TaintLedger
from services.agent.llm.client import ToolCallProposal
from services.agent.llm.tool_schemas import TOOL_NAME_OPERATION_MAP


def build_proposed_action(
    *,
    agent_id: str,
    session_id: UUID,
    user_request: str,
    proposal: ToolCallProposal,
    ledger: TaintLedger,
) -> ProposedAction:
    tool_name, operation = TOOL_NAME_OPERATION_MAP[proposal.function_name]

    sources = [
        UntrustedContentSource(source=e.source, content=e.content)
        for e in ledger.all()
    ]

    return ProposedAction(
        request_id=uuid4(),
        agent_id=agent_id,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc),
        tool_name=tool_name,
        operation=operation,
        arguments=proposal.arguments,
        target_resource=proposal.target_resource,
        destination=proposal.destination,
        context=ActionContext(
            user_request=user_request,
            untrusted_content_sources=sources,
        ),
    )
