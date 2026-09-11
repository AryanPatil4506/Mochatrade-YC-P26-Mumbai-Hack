"""tests/test_audit.py

Tests for the SQLite audit layer:
  - create / retrieve / list / update audit_logs
  - approval record CRUD
  - ALLOW, BLOCK, and approval flow paths (PART4.md sections 39-40)
"""
from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone

import pytest

from app.part4.database.db import close_connection, init_db
from app.part4.audit.models import AuditLog, ApprovalRecord
from app.part4.audit.service import AuditService
from app.part4.executor.model import DecisionObject, ExecutionResult, ProposedAction


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Each test gets its own fresh SQLite file."""
    db_file = str(tmp_path / "test_sentinel.db")
    init_db(db_file)
    yield db_file
    close_connection()
    # Unset env var so subsequent tests reinitialise cleanly
    os.environ.pop("DB_PATH", None)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _action(
    request_id: str = "req-audit-1",
    tool_name: str = "crm",
    operation: str = "update",
) -> ProposedAction:
    return ProposedAction(
        request_id=request_id,
        agent_id="agent-test",
        session_id="sess-test",
        timestamp=_now(),
        tool_name=tool_name,
        operation=operation,
        arguments={"status": "active"},
        target_resource="customer_001",
        destination=None,
        context={"user_request": "test", "untrusted_content_sources": []},
    )


def _decision(
    request_id: str = "req-audit-1",
    decision: str = "ALLOW",
    risk_score: int = 20,
    approval_id: str | None = None,
    audit_log_id: str | None = None,
    approval_status: str | None = None,
) -> DecisionObject:
    return DecisionObject(
        request_id=request_id,
        decision=decision,
        risk_score=risk_score,
        risk_factors={},
        policy_rule_triggered=None,
        explanation="test",
        requires_human_approval=(decision == "REQUIRE_APPROVAL"),
        approval_id=approval_id,
        timestamp=_now(),
        audit_log_id=audit_log_id or str(uuid.uuid4()),
        approval_status=approval_status,
    )


def _exec_result(
    request_id: str = "req-audit-1",
    executed: bool = True,
    success: bool = True,
    tool_name: str = "crm",
    operation: str = "update",
    error: str | None = None,
) -> ExecutionResult:
    return ExecutionResult(
        request_id=request_id,
        success=success,
        executed=executed,
        tool_name=tool_name,
        operation=operation,
        result={"success": success} if executed else None,
        error=error,
        executed_at=_now(),
    )


# ---------------------------------------------------------------------------
# AuditLog CRUD
# ---------------------------------------------------------------------------

class TestAuditLogCRUD:
    def test_create_and_retrieve_by_id(self):
        dec = _decision()
        log = AuditService.create_log(
            proposed_action=_action(),
            decision=dec,
            executed=True,
        )
        assert log.audit_log_id == dec.audit_log_id
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched is not None
        assert fetched.request_id == "req-audit-1"
        assert fetched.executed is True
        assert fetched.decision == "ALLOW"

    def test_retrieve_by_request_id(self):
        dec = _decision(request_id="req-xyz")
        AuditService.create_log(
            proposed_action=_action(request_id="req-xyz"),
            decision=dec,
            executed=False,
        )
        fetched = AuditService.get_log_by_request("req-xyz")
        assert fetched is not None
        assert fetched.agent_id == "agent-test"

    def test_retrieve_nonexistent_returns_none(self):
        assert AuditService.get_log("nonexistent-id") is None
        assert AuditService.get_log_by_request("nonexistent-req") is None

    def test_list_logs_unfiltered(self):
        for i in range(3):
            AuditService.create_log(
                proposed_action=_action(request_id=f"req-{i}"),
                decision=_decision(request_id=f"req-{i}"),
                executed=True,
            )
        logs = AuditService.list_logs()
        assert len(logs) == 3

    def test_list_logs_filter_by_decision(self):
        AuditService.create_log(
            proposed_action=_action(request_id="r1"),
            decision=_decision(request_id="r1", decision="ALLOW"),
            executed=True,
        )
        AuditService.create_log(
            proposed_action=_action(request_id="r2"),
            decision=_decision(request_id="r2", decision="BLOCK", risk_score=90),
            executed=False,
        )
        allow_logs = AuditService.list_logs(decision="ALLOW")
        block_logs = AuditService.list_logs(decision="BLOCK")
        assert len(allow_logs) == 1
        assert len(block_logs) == 1

    def test_list_logs_filter_by_tool_name(self):
        AuditService.create_log(
            proposed_action=_action(request_id="r1", tool_name="email"),
            decision=_decision(request_id="r1"),
            executed=True,
        )
        AuditService.create_log(
            proposed_action=_action(request_id="r2", tool_name="crm"),
            decision=_decision(request_id="r2"),
            executed=True,
        )
        email_logs = AuditService.list_logs(tool_name="email")
        assert len(email_logs) == 1
        assert email_logs[0].tool_name == "email"

    def test_update_resolution(self):
        dec = _decision()
        log = AuditService.create_log(
            proposed_action=_action(),
            decision=dec,
            executed=False,
        )
        updated = AuditService.update_resolution(
            log.audit_log_id, executed=True, resolved_at=_now()
        )
        assert updated is True
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is True
        assert fetched.resolved_at is not None

    def test_update_nonexistent_returns_false(self):
        updated = AuditService.update_resolution("ghost-id", executed=True)
        assert updated is False

    def test_to_dict_field_names_match_spec(self):
        """Verify all field names mandated by PART4.md section 19 are present."""
        dec = _decision()
        log = AuditService.create_log(
            proposed_action=_action(),
            decision=dec,
            executed=True,
        )
        d = log.to_dict()
        for field in [
            "audit_log_id", "request_id", "agent_id", "tool_name", "operation",
            "risk_score", "decision", "approval_id", "executed", "created_at", "resolved_at"
        ]:
            assert field in d, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# ALLOW flow (Test 1 from PART4.md section 39)
# ---------------------------------------------------------------------------

class TestAllowFlow:
    def test_allow_audit_executed_true(self):
        """ALLOW decision → executed=True in audit."""
        dec = _decision(decision="ALLOW", risk_score=20)
        log = AuditService.create_log(
            proposed_action=_action(),
            decision=dec,
            executed=True,
            resolved_at=_now(),
        )
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is True
        assert fetched.decision == "ALLOW"
        assert fetched.risk_score == 20

    def test_allow_execution_record_saved(self):
        """Execution record is persisted alongside the lifecycle log."""
        request_id = "req-allow-exec"
        exc_result = _exec_result(request_id=request_id, executed=True, success=True)
        AuditService.record_execution(request_id=request_id, execution_result=exc_result)
        records = AuditService.get_executions_for_request(request_id)
        assert len(records) == 1
        assert records[0].executed is True
        assert records[0].success is True


# ---------------------------------------------------------------------------
# BLOCK flow (Test 5 from PART4.md section 39)
# ---------------------------------------------------------------------------

class TestBlockFlow:
    def test_block_audit_executed_false(self):
        """BLOCK decision → executed=False in audit."""
        dec = _decision(decision="BLOCK", risk_score=90)
        log = AuditService.create_log(
            proposed_action=_action(tool_name="database", operation="delete"),
            decision=dec,
            executed=False,
        )
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is False
        assert fetched.decision == "BLOCK"

    def test_block_execution_record_not_executed(self):
        """Even when we record an execution event for a BLOCK, executed=False."""
        request_id = "req-block-exec"
        exc_result = _exec_result(
            request_id=request_id,
            executed=False,
            success=False,
            error="Execution blocked by authorization decision",
        )
        AuditService.record_execution(request_id=request_id, execution_result=exc_result)
        records = AuditService.get_executions_for_request(request_id)
        assert records[0].executed is False
        assert records[0].success is False


# ---------------------------------------------------------------------------
# Approval flows (Tests 2-4 from PART4.md section 39)
# ---------------------------------------------------------------------------

class TestApprovalFlows:
    def _setup_approval(self, approval_id: str, request_id: str) -> ApprovalRecord:
        return AuditService.create_approval(
            approval_id=approval_id,
            request_id=request_id,
            status="PENDING",
        )

    def test_require_approval_pending_executed_false(self):
        """REQUIRE_APPROVAL + PENDING → executed=False (Test 2)."""
        req_id = "req-approval-pending"
        appr_id = "appr-pending-1"
        self._setup_approval(appr_id, req_id)

        dec = _decision(
            request_id=req_id,
            decision="REQUIRE_APPROVAL",
            risk_score=70,
            approval_id=appr_id,
            approval_status="PENDING",
        )
        log = AuditService.create_log(
            proposed_action=_action(request_id=req_id),
            decision=dec,
            executed=False,
        )
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is False
        assert fetched.decision == "REQUIRE_APPROVAL"

        approval = AuditService.get_approval(appr_id)
        assert approval.status == "PENDING"

    def test_require_approval_approved_executed_true(self):
        """REQUIRE_APPROVAL + APPROVED → executed=True (Test 3)."""
        req_id = "req-approval-approved"
        appr_id = "appr-approved-1"
        self._setup_approval(appr_id, req_id)

        # Simulate Part 3 / human approval
        AuditService.resolve_approval(
            appr_id, status="APPROVED", approver_id="human-1", reason="Looks fine"
        )

        dec = _decision(
            request_id=req_id,
            decision="REQUIRE_APPROVAL",
            risk_score=70,
            approval_id=appr_id,
            approval_status="APPROVED",
        )
        log = AuditService.create_log(
            proposed_action=_action(request_id=req_id),
            decision=dec,
            executed=True,
            resolved_at=_now(),
        )
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is True

        approval = AuditService.get_approval(appr_id)
        assert approval.status == "APPROVED"
        assert approval.resolved_at is not None

    def test_require_approval_rejected_executed_false(self):
        """REQUIRE_APPROVAL + REJECTED → executed=False (Test 4)."""
        req_id = "req-approval-rejected"
        appr_id = "appr-rejected-1"
        self._setup_approval(appr_id, req_id)

        AuditService.resolve_approval(appr_id, status="REJECTED", reason="Too risky")

        dec = _decision(
            request_id=req_id,
            decision="REQUIRE_APPROVAL",
            risk_score=70,
            approval_id=appr_id,
            approval_status="REJECTED",
        )
        log = AuditService.create_log(
            proposed_action=_action(request_id=req_id),
            decision=dec,
            executed=False,
        )
        fetched = AuditService.get_log(log.audit_log_id)
        assert fetched.executed is False

        approval = AuditService.get_approval(appr_id)
        assert approval.status == "REJECTED"

    def test_approval_lifecycle_update_via_update_resolution(self):
        """
        Full lifecycle: PENDING → APPROVED → update audit log to executed=True.
        Models the flow in PART4.md section 21.
        """
        req_id = "req-lifecycle"
        appr_id = "appr-lifecycle-1"
        self._setup_approval(appr_id, req_id)

        # Initial log created when decision arrived (not yet executed)
        dec = _decision(
            request_id=req_id,
            decision="REQUIRE_APPROVAL",
            risk_score=70,
            approval_id=appr_id,
        )
        log = AuditService.create_log(
            proposed_action=_action(request_id=req_id),
            decision=dec,
            executed=False,
        )
        assert log.executed is False

        # Human approves
        AuditService.resolve_approval(appr_id, status="APPROVED", approver_id="manager-1")

        # Executor runs tool, then updates the audit record
        resolved_ts = _now()
        AuditService.update_resolution(log.audit_log_id, executed=True, resolved_at=resolved_ts)

        final = AuditService.get_log(log.audit_log_id)
        assert final.executed is True
        assert final.resolved_at == resolved_ts
        assert final.decision == "REQUIRE_APPROVAL"  # decision field unchanged

    def test_invalid_approval_status_raises(self):
        appr_id = "appr-invalid"
        AuditService.create_approval(approval_id=appr_id, request_id="req-x")
        with pytest.raises(ValueError, match="Invalid approval status"):
            AuditService.resolve_approval(appr_id, status="MAYBE")


# ---------------------------------------------------------------------------
# ExecutionRecord service helpers
# ---------------------------------------------------------------------------

class TestExecutionRecords:
    def test_record_and_retrieve(self):
        request_id = "req-exec-records"
        exc = _exec_result(request_id=request_id)
        rec = AuditService.record_execution(request_id=request_id, execution_result=exc)
        assert rec.request_id == request_id

        fetched = AuditService.get_executions_for_request(request_id)
        assert len(fetched) == 1
        assert fetched[0].executed is True

    def test_empty_request_returns_empty_list(self):
        assert AuditService.get_executions_for_request("no-such-request") == []
