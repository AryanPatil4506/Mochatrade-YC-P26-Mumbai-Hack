from __future__ import annotations

"""api/routes.py — Main FastAPI Application & Route Aggregator

Exposes Sentinel AI Part 4 API endpoints including the Attack Simulation Lab.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.attack_routes import attack_router


def create_app() -> FastAPI:
    """Application factory for Sentinel AI Part 4 service."""
    app = FastAPI(
        title="Sentinel AI — Part 4 Execution & Attack Simulation Lab",
        version="1.0.0",
        description=(
            "Provides sandbox execution enforcement, audit logging, and the Attack Simulation Lab "
            "for demonstration of Prompt Injection, Privilege Abuse, Destructive SQL, and Data Exfiltration."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the attack routes
    app.include_router(attack_router)

    @app.get("/health", tags=["System"])
    @app.get("/part4/health", tags=["System"])
    def health_check():
        return {
            "status": "healthy",
            "service": "sentinel-ai-part4",
            "attack_lab_available": True,
        }

    return app


app = create_app()
