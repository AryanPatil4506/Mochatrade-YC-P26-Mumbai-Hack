from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


class RiskFactors(BaseModel):
    tool_sensitivity: int = Field(0, ge=0, le=100, description="0-100 scale")
    data_sensitivity: int = Field(0, ge=0, le=100, description="0-100 scale")
    privilege_level: int = Field(0, ge=0, le=100, description="0-100 scale")
    destination_risk: int = Field(0, ge=0, le=100, description="0-100 scale")
    reversibility: int = Field(0, ge=0, le=100, description="0-100 scale")
    injection_signal: int = Field(0, ge=0, le=100, description="0-100 scale")
    behavioral_anomaly: int = Field(0, ge=0, le=100, description="0-100 scale")


class RiskResult(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_factors: RiskFactors = Field(default_factory=RiskFactors)
    provider_name: Optional[str] = Field("mock_risk_provider", description="Provider identifier")


class DecisionObject(BaseModel):
    request_id: UUID = Field(..., description="Corresponds to ProposedAction request_id")
    decision: DecisionEnum = Field(..., description="ALLOW | REQUIRE_APPROVAL | BLOCK")
    risk_score: int = Field(..., ge=0, le=100, description="Calculated or provided risk score 0-100")
    risk_factors: RiskFactors = Field(default_factory=RiskFactors)
    policy_rule_triggered: Optional[str] = Field(None, description="Identifier of policy rule triggered, or null")
    explanation: str = Field(..., description="Deterministic explanation of decision")
    requires_human_approval: bool = Field(False, description="True if decision is REQUIRE_APPROVAL")
    approval_id: Optional[UUID] = Field(None, description="UUID of approval record if requires_human_approval is True")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="ISO8601 timestamp")
    audit_log_id: UUID = Field(default_factory=uuid4, description="Audit log UUID for Part 4 traceability")

    def to_contract_dict(self) -> dict:
        """Converts to exact JSON contract format specified in Section 5."""
        return {
            "request_id": str(self.request_id),
            "decision": self.decision.value,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors.model_dump(),
            "policy_rule_triggered": self.policy_rule_triggered,
            "explanation": self.explanation,
            "requires_human_approval": self.requires_human_approval,
            "approval_id": str(self.approval_id) if self.approval_id else None,
            "timestamp": self.timestamp.isoformat(),
            "audit_log_id": str(self.audit_log_id)
        }
