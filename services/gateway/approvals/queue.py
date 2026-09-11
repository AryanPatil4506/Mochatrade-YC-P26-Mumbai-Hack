"""The human-approval queue for REQUIRE_APPROVAL decisions.

Persisted (not in-memory) so a resolve survives a gateway restart: the
original ProposedAction is stored as JSON alongside the approval row so a
capability token — bound to the *exact* arguments via args_sha256 — can be
issued when a human approves it later, without the caller having to resend
the action.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from packages.contracts.enums import ApprovalStatus
from packages.contracts.schemas import ApprovalRecord, Decision, ProposedAction
import services.executor.audit.repository as repo
from services.executor.audit import logger as audit_logger
from services.executor.audit.models import ApprovalRecord as StoredApproval
from services.gateway.decision.capability import issue_token


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_pending_approval(*, action: ProposedAction, decision: Decision) -> ApprovalRecord:
    approval_id = uuid4()
    stored = StoredApproval(
        approval_id=str(approval_id),
        request_id=str(action.request_id),
        status=ApprovalStatus.PENDING.value,
        created_at=_now_iso(),
        action_json=action.model_dump_json(),
        approver_id=None,
        reason=None,
        resolved_at=None,
        risk_score=decision.risk_score,
        risk_factors_json=json.dumps(decision.risk_factors.model_dump()),
    )
    repo.create_approval_record(stored)
    audit_logger.attach_approval(action.request_id, approval_id=approval_id)
    return _to_contract(stored)


def _to_contract(row: StoredApproval) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=UUID(row.approval_id),
        request_id=UUID(row.request_id),
        status=ApprovalStatus(row.status),
        approver_id=row.approver_id,
        reason=row.reason,
        resolved_at=datetime.fromisoformat(row.resolved_at) if row.resolved_at else None,
    )


def list_approvals(status: Optional[ApprovalStatus] = None) -> list[ApprovalRecord]:
    rows = repo.list_approval_records(status=status.value if status else None)
    return [_to_contract(r) for r in rows]


def get_approval(approval_id: UUID) -> Optional[ApprovalRecord]:
    row = repo.get_approval_record(str(approval_id))
    return _to_contract(row) if row else None


def resolve_approval(
    approval_id: UUID,
    *,
    status: ApprovalStatus,
    approver_id: Optional[str],
    reason: Optional[str],
) -> tuple[ApprovalRecord, Optional[str]]:
    """Returns (updated ApprovalRecord, capability_token or None). Raises
    KeyError if the approval doesn't exist, ValueError if it's already
    resolved (approvals are resolved exactly once)."""

    row = repo.get_approval_record(str(approval_id))
    if row is None:
        raise KeyError(str(approval_id))
    if row.status != ApprovalStatus.PENDING.value:
        raise ValueError(f"approval {approval_id} already resolved as {row.status}")

    resolved_at = _now_iso()
    repo.update_approval_record(
        str(approval_id), status=status.value, approver_id=approver_id, reason=reason, resolved_at=resolved_at
    )

    token = None
    if status == ApprovalStatus.APPROVED:
        action = ProposedAction.model_validate_json(row.action_json)
        token = issue_token(
            request_id=action.request_id,
            decision="APPROVED",
            tool_name=action.tool_name.value,
            operation=action.operation.value,
            arguments=action.arguments,
            target_resource=action.target_resource,
        )

    updated = repo.get_approval_record(str(approval_id))
    return _to_contract(updated), token
