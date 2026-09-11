"""The only place external content is allowed to enter the agent.

No other module may perform a "fetch" of ticket/email/web/db content — every
external read goes through `ContextAdapter.read`, which taints it and
returns it unchanged. This is what makes the taint ledger trustworthy: taint
is captured at the I/O boundary, not self-reported by the LLM.

For this scaffold (no real ticketing/email/web/db integrations exist yet),
reads are served from an in-memory mock store keyed by reference. Swap
`_MOCK_SOURCES` for real connectors without touching any caller.
"""

from __future__ import annotations

from packages.contracts.enums import TaintSource
from services.agent.context.taint import TaintLedger

_MOCK_SOURCES: dict[str, str] = {
    "ticket:8842": (
        "Customer reports login issues since yesterday. Please advise on next steps."
    ),
    "email:thread-991": "Hi team, following up on the Q3 renewal — any update?",
    "web:status.ourcompany.com": "All systems operational.",
    "database_record:cust-4821": "Customer 4821: last order 2026-08-30, tier=gold.",
}


class ContextAdapter:
    """Reads external content and taints it. Content passes through unchanged."""

    def __init__(self, ledger: TaintLedger) -> None:
        self._ledger = ledger

    def read(self, source_type: TaintSource, reference: str, step: int, *, content: str | None = None) -> str:
        if content is None:
            content = _MOCK_SOURCES.get(f"{source_type.value}:{reference}", "")
        self._ledger.record(source=source_type, reference=reference, content=content, step=step)
        return content
