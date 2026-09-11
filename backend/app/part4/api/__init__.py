from __future__ import annotations

"""api package â€” Sentinel AI Part 4 REST API."""

from app.part4.api.attack_routes import attack_router
from app.part4.api.execution_routes import execution_router

__all__ = ["attack_router", "execution_router"]
