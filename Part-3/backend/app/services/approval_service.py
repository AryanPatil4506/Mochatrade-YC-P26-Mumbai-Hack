from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.approval import ApprovalRecord
from app.schemas.action import ProposedAction
from app.schemas.approval import ApprovalRecordSchema, ApprovalStatus, ApprovalActionRequest
from app.schemas.decision import RiskResult


class ApprovalService:
    """
    Manages human approval requests and strict state machine transitions:
    PENDING -> APPROVED
    PENDING -> REJECTED
    Prevents modification of already-resolved records.
    """

    @staticmethod
    def create_pending_approval(
        db: Session,
        request_id: UUID,
        action: Optional[ProposedAction] = None,
        risk: Optional[RiskResult] = None,
        policy_name: Optional[str] = None
    ) -> ApprovalRecord:
        approval_id = str(uuid4())
        record = ApprovalRecord(
            approval_id=approval_id,
            request_id=str(request_id),
            status=ApprovalStatus.PENDING.value,
            approver_id=None,
            reason=None,
            created_at=datetime.now(timezone.utc),
            resolved_at=None,
            action_snapshot=action.model_dump_json_contract() if action else None,
            risk_snapshot=risk.model_dump() if risk else None,
            policy_snapshot=policy_name
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_pending_approvals(db: Session) -> List[ApprovalRecord]:
        return db.query(ApprovalRecord).filter(ApprovalRecord.status == ApprovalStatus.PENDING.value).all()

    @staticmethod
    def get_approval(db: Session, approval_id: UUID) -> ApprovalRecord:
        record = db.query(ApprovalRecord).filter(ApprovalRecord.approval_id == str(approval_id)).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request '{approval_id}' not found."
            )
        return record

    @staticmethod
    def approve(db: Session, approval_id: UUID, payload: ApprovalActionRequest) -> ApprovalRecord:
        record = ApprovalService.get_approval(db, approval_id)
        if record.status != ApprovalStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve request with status '{record.status}'. Only PENDING requests can be resolved."
            )

        record.status = ApprovalStatus.APPROVED.value
        record.approver_id = payload.approver_id
        record.reason = payload.reason
        record.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def reject(db: Session, approval_id: UUID, payload: ApprovalActionRequest) -> ApprovalRecord:
        record = ApprovalService.get_approval(db, approval_id)
        if record.status != ApprovalStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject request with status '{record.status}'. Only PENDING requests can be resolved."
            )

        record.status = ApprovalStatus.REJECTED.value
        record.approver_id = payload.approver_id
        record.reason = payload.reason
        record.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record
