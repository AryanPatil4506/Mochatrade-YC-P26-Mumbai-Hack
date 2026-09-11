from typing import List, Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.part3.database.database import get_db
from app.part3.schemas.approval import ApprovalRecordSchema, ApprovalActionRequest
from app.part3.services.approval_service import ApprovalService

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


class ApprovalDetailResponse(BaseModel):
    approval_id: UUID
    request_id: UUID
    status: str
    approver_id: Optional[str] = None
    reason: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: Optional[str] = None
    action_snapshot: Optional[Dict[str, Any]] = None
    risk_snapshot: Optional[Dict[str, Any]] = None
    policy_snapshot: Optional[str] = None


@router.get("/pending", response_model=List[ApprovalDetailResponse])
def list_pending_approvals(db: Session = Depends(get_db)):
    """Returns all approval requests currently in PENDING state."""
    records = ApprovalService.get_pending_approvals(db)
    return [
        ApprovalDetailResponse(
            approval_id=UUID(r.approval_id),
            request_id=UUID(r.request_id),
            status=r.status,
            approver_id=r.approver_id,
            reason=r.reason,
            resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
            created_at=r.created_at.isoformat() if r.created_at else None,
            action_snapshot=r.action_snapshot,
            risk_snapshot=r.risk_snapshot,
            policy_snapshot=r.policy_snapshot
        )
        for r in records
    ]


@router.get("/{approval_id}", response_model=ApprovalDetailResponse)
def get_approval(approval_id: UUID, db: Session = Depends(get_db)):
    """Returns a single approval request by approval_id."""
    r = ApprovalService.get_approval(db, approval_id)
    return ApprovalDetailResponse(
        approval_id=UUID(r.approval_id),
        request_id=UUID(r.request_id),
        status=r.status,
        approver_id=r.approver_id,
        reason=r.reason,
        resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
        created_at=r.created_at.isoformat() if r.created_at else None,
        action_snapshot=r.action_snapshot,
        risk_snapshot=r.risk_snapshot,
        policy_snapshot=r.policy_snapshot
    )


@router.post("/{approval_id}/approve", response_model=ApprovalRecordSchema)
def approve_request(
    approval_id: UUID,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    """Approves a PENDING approval request. Fails if already resolved."""
    record = ApprovalService.approve(db, approval_id, payload)
    return ApprovalRecordSchema(
        approval_id=UUID(record.approval_id),
        request_id=UUID(record.request_id),
        status=record.status,
        approver_id=record.approver_id,
        reason=record.reason,
        resolved_at=record.resolved_at
    )


@router.post("/{approval_id}/reject", response_model=ApprovalRecordSchema)
def reject_request(
    approval_id: UUID,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    """Rejects a PENDING approval request. Fails if already resolved."""
    record = ApprovalService.reject(db, approval_id, payload)
    return ApprovalRecordSchema(
        approval_id=UUID(record.approval_id),
        request_id=UUID(record.request_id),
        status=record.status,
        approver_id=record.approver_id,
        reason=record.reason,
        resolved_at=record.resolved_at
    )
