import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.part3.database.database import Base, get_db
from app.part3.database.seed import seed_agents
from app.main import app
from app.part3.schemas.action import ProposedAction, ActionContext, UntrustedContentSource


TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_agents(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_action():
    def _create(
        agent_id="support_agent",
        tool_name="crm",
        operation="read",
        target_resource="customers/101",
        destination=None,
        context=None
    ):
        return ProposedAction(
            request_id=uuid4(),
            agent_id=agent_id,
            session_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            tool_name=tool_name,
            operation=operation,
            arguments={"query": "active"},
            target_resource=target_resource,
            destination=destination,
            context=context or ActionContext(
                user_request="test query",
                untrusted_content_sources=[]
            )
        )
    return _create
