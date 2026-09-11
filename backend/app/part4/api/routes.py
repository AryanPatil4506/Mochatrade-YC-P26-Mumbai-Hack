"""Compatibility exports for callers that used the old Part 4 app module."""

from app.main import app, create_app

__all__ = ["app", "create_app"]
