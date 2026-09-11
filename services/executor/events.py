"""The single shared SSE event bus — "GET /v1/events, all services publish
here." Hosted on the executor since that's where the public endpoint table
lists it. The gateway pushes decision events in via a small
internal HTTP call (services/gateway/decision/events.py); the executor
publishes its own execution/token events directly by calling `publish()`
in-process. One in-memory fan-out queue per subscriber, matching the
"SSE is sufficient, no WebSocket infra" constraint.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

_subscribers: list[asyncio.Queue] = []


async def publish(event: dict[str, Any]) -> None:
    for q in list(_subscribers):
        await q.put(event)


async def subscribe() -> AsyncIterator[dict[str, Any]]:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)
    try:
        while True:
            yield await q.get()
    finally:
        _subscribers.remove(q)
