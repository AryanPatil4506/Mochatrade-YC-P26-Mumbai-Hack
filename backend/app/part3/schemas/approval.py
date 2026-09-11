from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRecordSchema(BaseModel):
    approval_id: UUID = Field(..., description="Unique approval identifier")
    request_id: UUID = Field(..., description="Referenced action request UUID")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="PENDING | APPROVED | REJECTED")
    approver_id: Optional[str] = Field(None, description="Identifier of human approver")
    reason: Optional[str] = Field(None, description="Resolution rationale or rejection reason")
    resolved_at: Optional[datetime] = Field(None, description="ISO8601 resolution timestamp")

    def to_contract_dict(self) -> dict:
        return {
            "approval_id": str(self.approval_id),
            "request_id": str(self.request_id),
            "status": self.status.value,
            "approver_id": self.approver_id,
            "reason": self.reason,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class ApprovalActionRequest(BaseModel):
    approver_id: str = Field(..., min_length=1, description="Approver user ID, e.g. admin_01")
    reason: str = Field(..., min_length=1, description="Reason for approving or rejecting")
