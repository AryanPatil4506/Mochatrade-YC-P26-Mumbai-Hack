from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.database.database import Base


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    approval_id = Column(String(36), primary_key=True, index=True)
    request_id = Column(String(36), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="PENDING", index=True)
    approver_id = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Optional metadata snapshot for fast approval queue display
    action_snapshot = Column(JSON, nullable=True)
    risk_snapshot = Column(JSON, nullable=True)
    policy_snapshot = Column(String(128), nullable=True)
