from __future__ import annotations

"""audit/service.py — AuditService

High-level facade used by the executor and API routes.
Keeps SQL persistence separate from execution logic (PART4.md section 26).
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from audit.models import ApprovalRecord, AuditLog, ExecutionRecord
import audit.repository as repo
from executor.model import DecisionObject, ExecutionResult, ProposedAction


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public AuditService interface
# ---------------------------------------------------------------------------

class AuditService:
    """
    One audit record per request lifecycle (PART4.md section 27).

    create_log        — write initial lifecycle record
    get_log           — retrieve by audit_log_id
    get_log_by_request — retrieve by request_id
    list_logs         — filtered list for dashboard
    update_resolution — update executed + resolved_at after approval completion
    """

    # ── Audit logs ───────────────────────────────────────────────────────────

    @staticmethod
    def create_log(
        *,
        proposed_action: ProposedAction,
        decision: DecisionObject,
        executed: bool,
        resolved_at: Optional[str] = None,
    ) -> AuditLog:
        """
        Persist one lifecycle record.

        If decision.audit_log_id is already set (provided by Part 3), honour it;
        otherwise generate a new UUID so Part 4 remains self-sufficient.
        """
        audit_log_id = decision.audit_log_id or str(uuid.uuid4())
        log = AuditLog(
            audit_log_id=audit_log_id,
            request_id=proposed_action.request_id,
            agent_id=proposed_action.agent_id,
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            risk_score=int(decision.risk_score),
            decision=decision.decision,
            approval_id=decision.approval_id,
            executed=executed,
            created_at=_now_iso(),
            resolved_at=resolved_at,
        )
        return repo.create_audit_log(log)

    @staticmethod
    def get_log(audit_log_id: str) -> Optional[AuditLog]:
        return repo.get_audit_log_by_id(audit_log_id)

    @staticmethod
    def get_log_by_request(request_id: str) -> Optional[AuditLog]:
        return repo.get_audit_log_by_request_id(request_id)

    @staticmethod
    def list_logs(
        *,
        decision: Optional[str] = None,
        tool_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[AuditLog]:
        return repo.list_audit_logs(
            decision=decision,
            tool_name=tool_name,
            agent_id=agent_id,
            limit=limit,
        )

    @staticmethod
    def update_resolution(
        audit_log_id: str,
        *,
        executed: bool,
        resolved_at: Optional[str] = None,
    ) -> bool:
        """Deliberately update executed + resolved_at (PART4.md section 45)."""
        ts = resolved_at or _now_iso()
        return repo.update_audit_log_resolution(
            audit_log_id, executed=executed, resolved_at=ts
        )

    # ── Approval records ─────────────────────────────────────────────────────

    @staticmethod
    def create_approval(
        *,
        approval_id: Optional[str] = None,
        request_id: str,
        status: str = "PENDING",
        approver_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> ApprovalRecord:
        rec = ApprovalRecord(
            approval_id=approval_id or str(uuid.uuid4()),
            request_id=request_id,
            status=status,
            approver_id=approver_id,
            reason=reason,
            resolved_at=None,
        )
        return repo.create_approval_record(rec)

    @staticmethod
    def get_approval(approval_id: str) -> Optional[ApprovalRecord]:
        return repo.get_approval_record(approval_id)

    @staticmethod
    def resolve_approval(
        approval_id: str,
        *,
        status: str,
        approver_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Set approval to APPROVED or REJECTED."""
        if status not in ("APPROVED", "REJECTED"):
            raise ValueError(f"Invalid approval status: {status!r}")
        return repo.update_approval_record(
            approval_id,
            status=status,
            approver_id=approver_id,
            reason=reason,
            resolved_at=_now_iso(),
        )

    # ── Execution records ────────────────────────────────────────────────────

    @staticmethod
    def record_execution(
        *,
        request_id: str,
        execution_result: ExecutionResult,
    ) -> ExecutionRecord:
        rec = ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            request_id=request_id,
            tool_name=execution_result.tool_name,
            operation=execution_result.operation,
            executed=execution_result.executed,
            success=execution_result.success,
            result=json.dumps(execution_result.result) if execution_result.result else None,
            error=execution_result.error,
            executed_at=execution_result.executed_at,
        )
        return repo.create_execution_record(rec)

    @staticmethod
    def get_executions_for_request(request_id: str) -> List[ExecutionRecord]:
        return repo.get_execution_records_for_request(request_id)
