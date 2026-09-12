"""The one in-path, non-authoritative LLM call: propose a tool call.

`temperature=0` and a fixed `seed` — model choice itself is a deliberately
changeable implementation detail. Output is untrusted input — re-validated
with Pydantic after the provider's own structured tool-call output. This
call decides nothing about risk or policy; it only proposes *what* the
agent would like to do next.

Provider: Groq (OpenAI-compatible chat completions API), reached with the
`openai` SDK pointed at Groq's base URL — no extra dependency needed. Model
and base URL are overridable via env vars so a demo machine can swap
providers without a code change.

If no `GROQ_API_KEY` is configured (e.g. running tests, or a demo machine
with no key set up), `propose_tool_call` falls back to a small deterministic
keyword-matching stub so the rest of the graph is exercisable offline. This
fallback is clearly a dev convenience, not a second code path used in the
real pipeline's decision-relevant logic.
"""

from __future__ import annotations

import json
import os
from pydantic import BaseModel, ConfigDict, ValidationError

from services.agent.llm.prompts import SYSTEM_PROMPT, build_user_turn
from services.agent.llm.tool_schemas import TOOL_FUNCTIONS, TOOL_NAME_OPERATION_MAP

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
FIXED_SEED = 7


class ToolCallProposal(BaseModel):
    """Revalidated shape of what the model proposed. Untrusted until this
    passes — and even after, it carries no authority over the decision.
    """

    model_config = ConfigDict(extra="forbid")

    function_name: str
    arguments: dict
    target_resource: str
    destination: str | None = None

    def validate_known_tool(self) -> None:
        if self.function_name not in TOOL_NAME_OPERATION_MAP:
            raise ValueError(f"unknown tool function: {self.function_name}")


def _stub_propose(user_request: str) -> ToolCallProposal:
    """Deterministic offline fallback used only when no API key is set."""

    lowered = user_request.lower()
    if "email" in lowered or "send" in lowered:
        return ToolCallProposal(
            function_name="email_send",
            arguments={"to": "unspecified@example.com", "subject": "Re: request", "body": user_request},
            target_resource="email.outbox",
            destination="unspecified@example.com",
        )
    if "delete" in lowered:
        return ToolCallProposal(
            function_name="database_delete",
            arguments={"table": "customers"},
            target_resource="customers",
            destination=None,
        )
    return ToolCallProposal(
        function_name="crm_read",
        arguments={"contact_id": "unknown"},
        target_resource="crm.contacts",
        destination=None,
    )


def propose_tool_call(user_request: str, observed_context: list[str]) -> ToolCallProposal:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return _stub_propose(user_request)

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        seed=FIXED_SEED,
        tools=TOOL_FUNCTIONS,
        tool_choice="required",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_turn(user_request, observed_context)},
        ],
    )

    tool_call = response.choices[0].message.tool_calls[0]
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as exc:
        raise ValueError("model returned non-JSON tool arguments") from exc

    target_resource = arguments.pop("target_resource", None) or arguments.get("table") or arguments.get("contact_id") or arguments.get("ticket_id") or "unknown"
    destination = arguments.pop("destination", None) or arguments.get("to")

    proposal = ToolCallProposal(
        function_name=tool_call.function.name,
        arguments=arguments,
        target_resource=target_resource,
        destination=destination,
    )
    proposal.validate_known_tool()
    return proposal
