"""SQLite persistence for audit logs, approval records, and execution
records. Pure CRUD — no business logic (that's logger.py / the gateway's
approvals queue)."""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from services.executor.audit.models import ApprovalRecord, AuditLog, ExecutionRecord
from services.executor.audit.store import get_connection


def _row_to_audit(row: sqlite3.Row) -> AuditLog:
    return AuditLog(
        audit_log_id=row["audit_log_id"],
        request_id=row["request_id"],
        agent_id=row["agent_id"],
        tool_name=row["tool_name"],
        operation=row["operation"],
        risk_score=row["risk_score"],
        decision=row["decision"],
        approval_id=row["approval_id"],
        executed=bool(row["executed"]),
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
    )


def _row_to_approval(row: sqlite3.Row) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=row["approval_id"],
        request_id=row["request_id"],
        status=row["status"],
        created_at=row["created_at"],
        action_json=row["action_json"],
        approver_id=row["approver_id"],
        reason=row["reason"],
        resolved_at=row["resolved_at"],
        risk_score=row["risk_score"],
        risk_factors_json=row["risk_factors_json"],
    )


def _row_to_execution(row: sqlite3.Row) -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=row["execution_id"],
        request_id=row["request_id"],
        tool_name=row["tool_name"],
        operation=row["operation"],
        executed=bool(row["executed"]),
        success=bool(row["success"]),
        result=row["result"],
        error=row["error"],
        executed_at=row["executed_at"],
    )


# --- audit_logs --------------------------------------------------------

def create_audit_log(log: AuditLog) -> AuditLog:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO audit_logs
            (audit_log_id, request_id, agent_id, tool_name, operation,
             risk_score, decision, approval_id, executed, created_at, resolved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log.audit_log_id, log.request_id, log.agent_id, log.tool_name, log.operation,
            log.risk_score, log.decision, log.approval_id, int(log.executed),
            log.created_at, log.resolved_at,
        ),
    )
    conn.commit()
    return log


def get_audit_log_by_id(audit_log_id: str) -> Optional[AuditLog]:
    row = get_connection().execute(
        "SELECT * FROM audit_logs WHERE audit_log_id = ?", (audit_log_id,)
    ).fetchone()
    return _row_to_audit(row) if row else None


def get_audit_log_by_request_id(request_id: str) -> Optional[AuditLog]:
    row = get_connection().execute(
        "SELECT * FROM audit_logs WHERE request_id = ?", (request_id,)
    ).fetchone()
    return _row_to_audit(row) if row else None


def list_audit_logs(
    *,
    decision: Optional[str] = None,
    tool_name: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 200,
) -> List[AuditLog]:
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params: list = []
    if decision:
        query += " AND decision = ?"
        params.append(decision)
    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)
    if agent_id:
        query += " AND agent_id = ?"
        params.append(agent_id)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = get_connection().execute(query, params).fetchall()
    return [_row_to_audit(r) for r in rows]


def update_audit_log_resolution(audit_log_id: str, *, executed: bool, resolved_at: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE audit_logs SET executed = ?, resolved_at = ? WHERE audit_log_id = ?",
        (int(executed), resolved_at, audit_log_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def update_audit_log_approval(audit_log_id: str, *, approval_id: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE audit_logs SET approval_id = ? WHERE audit_log_id = ?",
        (approval_id, audit_log_id),
    )
    conn.commit()
    return cursor.rowcount > 0


# --- approval_records ----------------------------------------------------

def create_approval_record(rec: ApprovalRecord) -> ApprovalRecord:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO approval_records
            (approval_id, request_id, status, approver_id, reason, resolved_at,
             created_at, action_json, risk_score, risk_factors_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rec.approval_id, rec.request_id, rec.status, rec.approver_id, rec.reason,
            rec.resolved_at, rec.created_at, rec.action_json, rec.risk_score, rec.risk_factors_json,
        ),
    )
    conn.commit()
    return rec


def get_approval_record(approval_id: str) -> Optional[ApprovalRecord]:
    row = get_connection().execute(
        "SELECT * FROM approval_records WHERE approval_id = ?", (approval_id,)
    ).fetchone()
    return _row_to_approval(row) if row else None


def list_approval_records(*, status: Optional[str] = None, limit: int = 200) -> List[ApprovalRecord]:
    query = "SELECT * FROM approval_records WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = get_connection().execute(query, params).fetchall()
    return [_row_to_approval(r) for r in rows]


def update_approval_record(
    approval_id: str,
    *,
    status: str,
    approver_id: Optional[str] = None,
    reason: Optional[str] = None,
    resolved_at: Optional[str] = None,
) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        """
        UPDATE approval_records
        SET status = ?, approver_id = ?, reason = ?, resolved_at = ?
        WHERE approval_id = ?
        """,
        (status, approver_id, reason, resolved_at, approval_id),
    )
    conn.commit()
    return cursor.rowcount > 0


# --- execution_records -----------------------------------------------------

def create_execution_record(rec: ExecutionRecord) -> ExecutionRecord:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO execution_records
            (execution_id, request_id, tool_name, operation, executed, success, result, error, executed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rec.execution_id, rec.request_id, rec.tool_name, rec.operation,
            int(rec.executed), int(rec.success), rec.result, rec.error, rec.executed_at,
        ),
    )
    conn.commit()
    return rec


def get_execution_records_for_request(request_id: str) -> List[ExecutionRecord]:
    rows = get_connection().execute(
        "SELECT * FROM execution_records WHERE request_id = ? ORDER BY executed_at ASC",
        (request_id,),
    ).fetchall()
    return [_row_to_execution(r) for r in rows]


# --- used_tokens (capability token replay guard) ----------------------------

def jti_seen(jti: str) -> bool:
    row = get_connection().execute(
        "SELECT 1 FROM used_tokens WHERE jti = ?", (jti,)
    ).fetchone()
    return row is not None


def mark_jti_used(jti: str, *, used_at: str) -> None:
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO used_tokens (jti, used_at) VALUES (?, ?)", (jti, used_at))
    conn.commit()
