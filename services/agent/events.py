"""In-memory SSE event bus for the agent service.

One `asyncio.Queue` per session. Nodes call `publish()` as the graph runs;
`GET /v1/agent/sessions/{id}` (via `/v1/events`-style streaming, see api.py)
reads from `subscribe()`. No polling, no external broker — SSE is sufficient
here, no WebSocket infrastructure needed.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator
from uuid import UUID

_queues: dict[UUID, list[asyncio.Queue]] = defaultdict(list)


async def publish(session_id: UUID, event: dict[str, Any]) -> None:
    for q in list(_queues.get(session_id, [])):
        await q.put(event)


async def subscribe(session_id: UUID) -> AsyncIterator[dict[str, Any]]:
    q: asyncio.Queue = asyncio.Queue()
    _queues[session_id].append(q)
    try:
        while True:
            event = await q.get()
            yield event
            if event.get("type") == "session_closed":
                break
    finally:
        _queues[session_id].remove(q)
