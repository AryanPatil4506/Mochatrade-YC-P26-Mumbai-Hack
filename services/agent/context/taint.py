"""In-memory taint ledger for one agent session.

Every external read must go through `ContextAdapter.read` (see adapter.py),
which appends here. The ledger is the only source of truth for
`ProposedAction.context.untrusted_content_sources` — never LLM-reported,
because a manipulated model is the wrong narrator of its own manipulation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from packages.contracts.enums import TaintSource
from packages.contracts.schemas import TaintEntry

TRANSPORT_TRUNCATE_CHARS = 8_000


class TaintLedger:
    """Append-only per-session record of every untrusted read."""

    def __init__(self) -> None:
        self._entries: list[TaintEntry] = []

    def record(self, source: TaintSource, reference: str, content: str, step: int) -> TaintEntry:
        entry = TaintEntry(
            entry_id=uuid4(),
            source=source,
            reference=reference,
            content=content,
            read_at=datetime.now(timezone.utc),
            step=step,
        )
        self._entries.append(entry)
        return entry

    def all(self) -> list[TaintEntry]:
        return list(self._entries)

    def since_step(self, step: int) -> list[TaintEntry]:
        return [e for e in self._entries if e.step >= step]

    def as_untrusted_content_sources(self) -> list[dict]:
        """Transport-ready shape for ProposedAction.context.untrusted_content_sources.

        Truncated at TRANSPORT_TRUNCATE_CHARS per entry for transport; the
        full text was already scanned (by detectors, in Part 2) before this
        truncation happens.
        """

        return [
            {"source": e.source.value, "content": e.content[:TRANSPORT_TRUNCATE_CHARS]}
            for e in self._entries
        ]
