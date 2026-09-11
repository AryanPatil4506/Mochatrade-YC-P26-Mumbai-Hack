"""Internal storage dataclasses for the executor's SQLite tables.

These are NOT the frozen wire contracts (packages.contracts.schemas). They
mirror AuditLogEntry/ApprovalRecord field-for-field plus a few
executor-internal columns (see schema.sql) used to reissue capability tokens
and to persist a snapshot for the dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditLog:
    audit_log_id: str
    request_id: str
    agent_id: str
    tool_name: str
    operation: str
    risk_score: int
    decision: str
    approval_id: Optional[str]
    executed: bool
    created_at: str
    resolved_at: Optional[str]

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
    approval_id: str
    request_id: str
    status: str
    created_at: str
    action_json: str
    approver_id: Optional[str] = None
    reason: Optional[str] = None
    resolved_at: Optional[str] = None
    risk_score: Optional[int] = None
    risk_factors_json: Optional[str] = None


@dataclass
class ExecutionRecord:
    execution_id: str
    request_id: str
    tool_name: str
    operation: str
    executed: bool
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    executed_at: Optional[str] = None
