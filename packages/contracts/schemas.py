"""Frozen shared contracts between Part 1 (agent), Part 2 (detection), Part 3
(policy/decision), and Part 4 (executor).

Do not rename, add, or remove fields without explicit sign-off from all four
parts. Every model rejects unknown fields (`extra="forbid"`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import ApprovalStatus, DecisionValue, DetectorMode, Operation, TaintSource, ToolName

_FACTOR_NAMES = (
    "tool_sensitivity",
    "data_sensitivity",
    "privilege_level",
    "destination_risk",
    "reversibility",
    "injection_signal",
    "behavioral_anomaly",
)


class UntrustedContentSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: TaintSource
    content: str


class ActionContext(BaseModel):
    """`context` block of ProposedAction."""

    model_config = ConfigDict(extra="forbid")

    user_request: str
    untrusted_content_sources: list[UntrustedContentSource] = Field(default_factory=list)


class ProposedAction(BaseModel):
    """Part 1 (agent) -> Gateway.

    Server-controlled fields the model never sets: `request_id`, `timestamp`,
    `agent_id`. `tool_name` / `operation` derive from a fixed tool-name
    mapping, never asked of the model. `context.untrusted_content_sources`
    is built by `ContextAdapter`, never model-supplied.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    agent_id: str
    session_id: UUID
    timestamp: datetime
    tool_name: ToolName
    operation: Operation
    arguments: dict
    target_resource: str
    destination: str | None = None
    context: ActionContext


class RiskFactors(BaseModel):
    """The seven risk factor keys. Each is an int in [0, 100]."""

    model_config = ConfigDict(extra="forbid")

    tool_sensitivity: int = Field(ge=0, le=100)
    data_sensitivity: int = Field(ge=0, le=100)
    privilege_level: int = Field(ge=0, le=100)
    destination_risk: int = Field(ge=0, le=100)
    reversibility: int = Field(ge=0, le=100)
    injection_signal: int = Field(ge=0, le=100)
    behavioral_anomaly: int = Field(ge=0, le=100)


class RiskEvidence(BaseModel):
    """Display-only. Never influences the decision."""

    model_config = ConfigDict(extra="forbid")

    injection_families: list[str] = Field(default_factory=list)
    detected_entity_types: list[str] = Field(default_factory=list)
    record_count_estimate: int = 0
    intent_drift: float = 0.0
    detector_mode: DetectorMode = DetectorMode.RULES_AND_CLASSIFIER


class RiskAssessment(BaseModel):
    """Part 2 (detection) -> Part 3 (decision). Additive contract."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    risk_factors: RiskFactors
    risk_score: int = Field(ge=0, le=100)
    escalation_floor_triggered: str | None = None
    evidence: RiskEvidence
    computed_at: datetime
    engine_version: str


class Decision(BaseModel):
    """Part 3 (decision) -> everyone.

    `requires_human_approval` is derived, never set independently: a
    `model_validator` overwrites it to `decision == REQUIRE_APPROVAL`
    regardless of what was passed in, on every construction *and* every
    revalidation (`model_validate` / `model_validate_json`). It is a plain
    field (not a `computed_field`) specifically so it survives round-tripping
    through the wire format on models with `extra="forbid"` — a
    `computed_field` is serialized on the way out but rejected as an unknown
    field on the way back in, which breaks exactly the real gateway-response
    -> agent-revalidation path this contract exists for.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    decision: DecisionValue
    risk_score: int = Field(ge=0, le=100)
    risk_factors: RiskFactors
    policy_rule_triggered: str | None = None
    explanation: str | None = None
    requires_human_approval: bool = False
    capability_token: str | None = None
    timestamp: datetime
    audit_log_id: UUID

    @model_validator(mode="after")
    def _derive_requires_human_approval(self) -> "Decision":
        self.requires_human_approval = self.decision == DecisionValue.REQUIRE_APPROVAL
        return self

    @classmethod
    def fail_closed(cls, request_id: UUID) -> "Decision":
        """The fixed BLOCK payload used on any gateway timeout/error.

        Fail closed, never fail open. This is a pure constructor for the
        frozen contract shape — it does not itself decide anything.
        """

        zero_factors = RiskFactors(**{name: 0 for name in _FACTOR_NAMES})
        return cls(
            request_id=request_id,
            decision=DecisionValue.BLOCK,
            risk_score=100,
            risk_factors=zero_factors,
            policy_rule_triggered="gateway_unavailable",
            explanation=None,
            capability_token=None,
            timestamp=datetime.now(timezone.utc),
            audit_log_id=uuid4(),
        )


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: UUID
    request_id: UUID
    status: ApprovalStatus
    approver_id: str | None = None
    reason: str | None = None
    resolved_at: datetime | None = None


class AuditLogEntry(BaseModel):
    """One row per `request_id`, updated in place."""

    model_config = ConfigDict(extra="forbid")

    audit_log_id: UUID
    request_id: UUID
    agent_id: str
    tool_name: str
    operation: str
    risk_score: int = Field(ge=0, le=100)
    decision: str
    approval_id: UUID | None = None
    executed: bool
    created_at: datetime
    resolved_at: datetime | None = None


class TaintEntry(BaseModel):
    """Internal to Part 1."""

    model_config = ConfigDict(extra="forbid")

    entry_id: UUID
    source: TaintSource
    reference: str
    content: str
    read_at: datetime
    step: int
