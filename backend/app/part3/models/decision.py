from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from app.part3.database.database import Base


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False)
    agent_id = Column(String(64), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False)
    operation = Column(String(64), nullable=False)
    target_resource = Column(String(256), nullable=False)
    destination = Column(String(256), nullable=True)
    raw_action = Column(JSON, nullable=False)

    decision = Column(String(32), nullable=False, index=True)  # ALLOW, REQUIRE_APPROVAL, BLOCK
    risk_score = Column(Integer, nullable=False)
    risk_factors = Column(JSON, nullable=False)
    policy_rule_triggered = Column(String(128), nullable=True)
    explanation = Column(Text, nullable=False)
    requires_human_approval = Column(Boolean, default=False, nullable=False)
    approval_id = Column(String(36), nullable=True, index=True)
    audit_log_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
