from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AuditLog:
    """Exact contract from PART4.md section 19. Field names MUST NOT change."""

    audit_log_id: str
    request_id: str
    agent_id: str
    tool_name: str
    operation: str
    risk_score: int
    decision: str          # ALLOW | REQUIRE_APPROVAL | BLOCK
    approval_id: Optional[str]
    executed: bool
    created_at: str        # ISO8601
    resolved_at: Optional[str]  # ISO8601 or None

    def to_dict(self) -> dict:
        return {
            "audit_log_id": self.audit_log_id,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "risk_score": self.risk_score,
            "decision": self.decision,
            "approval_id": self.approval_id,
            "executed": self.executed,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


@dataclass
class ApprovalRecord:
    """Approval workflow record.  Part 3 owns creation; Part 4 reads status."""

    approval_id: str
    request_id: str
    status: str            # PENDING | APPROVED | REJECTED
    approver_id: Optional[str] = None
    reason: Optional[str] = None
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "request_id": self.request_id,
            "status": self.status,
            "approver_id": self.approver_id,
            "reason": self.reason,
            "resolved_at": self.resolved_at,
        }


@dataclass
class ExecutionRecord:
    """Per-tool execution event, separate from the lifecycle audit_log."""

    execution_id: str
    request_id: str
    tool_name: str
    operation: str
    executed: bool
    success: bool
    result: Optional[str] = None   # JSON string
    error: Optional[str] = None
    executed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "executed": self.executed,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at,
        }
