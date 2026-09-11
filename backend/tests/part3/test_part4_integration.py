import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.part3.schemas.action import ProposedAction
from app.part3.schemas.decision import DecisionEnum, DecisionObject
from app.part4.audit.service import AuditService
from app.part4.database.db import close_connection, init_db
from app.integration import execute_part3_decision


@pytest.fixture(autouse=True)
def isolated_part4_db(tmp_path):
    init_db(str(tmp_path / "part4-integration.db"))
    yield
    close_connection()
    os.environ.pop("DB_PATH", None)


def make_action():
    return ProposedAction(
        request_id=uuid4(),
        agent_id="support_agent",
        session_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        tool_name="crm",
        operation="update",
        arguments={"status": "verified"},
        target_resource="customer_123",
    )


def make_decision(action, decision, approval_id=None):
    return DecisionObject(
        request_id=action.request_id,
        decision=decision,
        risk_score=20,
        explanation="deterministic test decision",
        requires_human_approval=decision == DecisionEnum.REQUIRE_APPROVAL,
        approval_id=approval_id,
    )


def test_allow_executes_and_audits():
    action = make_action()
    result = execute_part3_decision(action, make_decision(action, DecisionEnum.ALLOW))

    assert result["execution"]["executed"] is True
    assert result["audit"]["request_id"] == str(action.request_id)
    assert result["audit"]["executed"] is True
    assert AuditService.get_log_by_request(str(action.request_id)) is not None


def test_require_approval_executes_only_when_approved():
    pending_action = make_action()
    approval_id = str(uuid4())
    decision = make_decision(pending_action, DecisionEnum.REQUIRE_APPROVAL, approval_id)
    pending = execute_part3_decision(
        pending_action,
        decision,
        approval_status="PENDING",
    )
    assert pending["execution"]["executed"] is False
    assert pending["audit"]["executed"] is False

    approved = execute_part3_decision(
        pending_action,
        decision,
        approval_status="APPROVED",
    )
    assert approved["execution"]["executed"] is True
    assert approved["audit"]["executed"] is True


def test_block_never_executes_but_is_audited():
    action = make_action()
    result = execute_part3_decision(action, make_decision(action, DecisionEnum.BLOCK))

    assert result["execution"]["executed"] is False
    assert result["audit"]["decision"] == "BLOCK"
    assert result["audit"]["executed"] is False