"""High-level audit facade used by the gateway (to open a lifecycle record at
decision time) and the executor (to close it out at execution time). Keeps
SQL persistence (repository.py) separate from when/why a row gets written.

One row per request_id, updated in place — per CLAUDE.md's AuditLogEntry
contract. `executed` starts False and only ever flips to True when a sandbox
tool actually ran.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import services.executor.audit.repository as repo
from services.executor.audit.models import AuditLog, ExecutionRecord
from packages.contracts.schemas import Decision, ProposedAction


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_log(*, action: ProposedAction, decision: Decision, executed: bool = False) -> AuditLog:
    """Open the lifecycle record for a request_id. Idempotent: a duplicate
    request_id (same audit_log_id) returns the existing row rather than
    inserting twice, matching the frozen idempotency requirement."""

    existing = repo.get_audit_log_by_id(str(decision.audit_log_id))
    if existing is not None:
        return existing

    log = AuditLog(
        audit_log_id=str(decision.audit_log_id),
        request_id=str(action.request_id),
        agent_id=action.agent_id,
        tool_name=action.tool_name.value,
        operation=action.operation.value,
        risk_score=decision.risk_score,
        decision=decision.decision.value,
        approval_id=None,
        executed=executed,
        created_at=_now_iso(),
        resolved_at=None,
    )
    return repo.create_audit_log(log)


def attach_approval(request_id: UUID, *, approval_id: UUID) -> None:
    log = repo.get_audit_log_by_request_id(str(request_id))
    if log is not None:
        repo.update_audit_log_approval(log.audit_log_id, approval_id=str(approval_id))


def mark_executed(request_id: UUID, *, executed: bool, resolved_at: Optional[str] = None) -> None:
    log = repo.get_audit_log_by_request_id(str(request_id))
    if log is None:
        return
    repo.update_audit_log_resolution(log.audit_log_id, executed=executed, resolved_at=resolved_at or _now_iso())


def record_token_failure(action: ProposedAction, *, reason: str) -> None:
    """A forged/expired/replayed/mismatched token means no prior Decision may
    exist for this request_id (a compromised agent can call /v1/execute
    directly, bypassing the gateway). Create-or-touch the row so the
    compromised-agent test's `executed: false` assertion has something to
    read; CLAUDE.md's AuditLogEntry has no policy_rule_triggered field, so
    that reason is reported in the 403 body, not persisted here."""

    existing = repo.get_audit_log_by_request_id(str(action.request_id))
    if existing is not None:
        # Never downgrade a row that already recorded a real execution (e.g. a
        # replay attempt against an already-consumed, legitimately-used
        # token must not erase the fact that the original call executed).
        if not existing.executed:
            repo.update_audit_log_resolution(existing.audit_log_id, executed=False, resolved_at=_now_iso())
        return

    log = AuditLog(
        audit_log_id=str(action.request_id),
        request_id=str(action.request_id),
        agent_id=action.agent_id,
        tool_name=action.tool_name.value,
        operation=action.operation.value,
        risk_score=100,
        decision="BLOCK",
        approval_id=None,
        executed=False,
        created_at=_now_iso(),
        resolved_at=_now_iso(),
    )
    repo.create_audit_log(log)


def record_execution(*, request_id: UUID, tool_name: str, operation: str, executed: bool,
                      success: bool, result: Optional[dict], error: Optional[str], executed_at: str) -> None:
    from uuid import uuid4

    repo.create_execution_record(
        ExecutionRecord(
            execution_id=str(uuid4()),
            request_id=str(request_id),
            tool_name=tool_name,
            operation=operation,
            executed=executed,
            success=success,
            result=json.dumps(result) if result is not None else None,
            error=error,
            executed_at=executed_at,
        )
    )


def get_by_request(request_id: UUID | str) -> Optional[AuditLog]:
    return repo.get_audit_log_by_request_id(str(request_id))


def list_timeline(*, limit: int = 50) -> list[AuditLog]:
    return repo.list_audit_logs(limit=limit)
