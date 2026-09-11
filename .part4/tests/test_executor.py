from datetime import datetime, timezone

from executor.executor import execute_request
from executor.model import DecisionObject, ProposedAction


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _action(request_id="req-123", tool_name="crm", operation="update"):
    return ProposedAction(
        request_id=request_id,
        agent_id="agent-1",
        session_id="sess-1",
        timestamp=_now_iso(),
        tool_name=tool_name,
        operation=operation,
        arguments={"status": "verified"},
        target_resource="customer_123",
        destination=None,
        context={
            "user_request": "Update customer status",
            "untrusted_content_sources": [],
        },
    )


def _decision(request_id="req-123", decision="ALLOW", approval_status=None):
    return DecisionObject(
        request_id=request_id,
        decision=decision,
        risk_score=0,
        risk_factors={},
        policy_rule_triggered=None,
        explanation="Test decision",
        requires_human_approval=(decision == "REQUIRE_APPROVAL"),
        approval_id="approval-1" if decision == "REQUIRE_APPROVAL" else None,
        timestamp=_now_iso(),
        audit_log_id="audit-1",
        approval_status=approval_status,
    )


def test_allow_executes_tool():
    result = execute_request(_action(), _decision())

    assert result.executed is True
    assert result.success is True
    assert result.tool_name == "crm"
    assert result.result["success"] is True
    assert result.error is None


def test_require_approval_pending_does_not_execute():
    result = execute_request(_action(), _decision(decision="REQUIRE_APPROVAL", approval_status="PENDING"))

    assert result.executed is False
    assert result.success is False
    assert result.result is None
    assert "approval" in (result.error or "").lower()


def test_require_approval_approved_executes_tool():
    result = execute_request(_action(), _decision(decision="REQUIRE_APPROVAL", approval_status="APPROVED"))

    assert result.executed is True
    assert result.success is True
    assert result.tool_name == "crm"


def test_require_approval_rejected_does_not_execute():
    result = execute_request(_action(), _decision(decision="REQUIRE_APPROVAL", approval_status="REJECTED"))

    assert result.executed is False
    assert result.success is False
    assert result.result is None


def test_block_never_executes_even_if_approved():
    result = execute_request(_action(), _decision(decision="BLOCK", approval_status="APPROVED"))

    assert result.executed is False
    assert result.success is False
    assert result.error == "Execution blocked by authorization decision"


def test_invalid_request_id_mismatch_is_rejected():
    result = execute_request(_action(request_id="req-1"), _decision(request_id="req-2"))

    assert result.executed is False
    assert result.success is False
    assert "request id" in (result.error or "").lower()


def test_unknown_tool_is_rejected_by_registry():
    result = execute_request(_action(tool_name="unknown_tool"), _decision())

    assert result.executed is False
    assert result.success is False
    assert "not allowed" in (result.error or "").lower()
