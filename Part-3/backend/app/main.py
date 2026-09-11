from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.database import engine, Base, SessionLocal
from app.database.seed import seed_agents
from app.api import evaluate_router, approvals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist & initial agents/permissions are seeded
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_agents(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Sentinel AI — Runtime Security Gateway (Part 3)",
    version="1.0.0",
    description="Deterministic Authorization, Least-Privilege & Policy Engine for Autonomous AI Agents",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(evaluate_router)
app.include_router(approvals_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Sentinel AI Part 3 Runtime Security Gateway",
        "version": "1.0.0",
        "allow_threshold": settings.ALLOW_THRESHOLD,
        "approval_threshold": settings.APPROVAL_THRESHOLD,
        "risk_provider": settings.RISK_PROVIDER
    }
