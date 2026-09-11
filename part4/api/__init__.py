from __future__ import annotations

"""api package — Sentinel AI Part 4 REST API."""

from api.attack_routes import attack_router
from api.routes import app, create_app

__all__ = ["app", "create_app", "attack_router"]
