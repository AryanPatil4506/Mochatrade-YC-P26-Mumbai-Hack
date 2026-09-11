from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.part3.api import approvals_router, evaluate_router
from app.part3.database.database import Base, SessionLocal, engine
from app.part3.database.seed import seed_agents
from app.part4.api.attack_routes import attack_router
from app.part4.api.execution_routes import execution_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_agents(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sentinel AI Unified Runtime Security Backend",
        version="1.0.0",
        description=(
            "Unified Part 3 policy and approval gateway with Part 4 sandbox execution, "
            "audit logging, and attack simulation."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(evaluate_router)
    app.include_router(approvals_router)
    app.include_router(attack_router)
    app.include_router(execution_router)

    @app.get("/health", tags=["System"])
    @app.get("/part4/health", tags=["System"])
    def health_check():
        return {
            "status": "healthy",
            "service": "sentinel-ai-unified-backend",
            "part3_available": True,
            "part4_available": True,
            "attack_lab_available": True,
            "allow_threshold": settings.ALLOW_THRESHOLD,
            "approval_threshold": settings.APPROVAL_THRESHOLD,
            "risk_provider": settings.RISK_PROVIDER,
        }

    return app


app = create_app()
