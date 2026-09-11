from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.models.decision import DecisionRecord
from app.schemas.action import ProposedAction
from app.schemas.decision import DecisionObject, DecisionEnum, RiskResult, RiskFactors
from app.services.approval_service import ApprovalService
from app.services.mock_risk_provider import MockRiskProvider
from app.services.permission_service import check_agent_permission
from app.services.policy_engine import PolicyEngine
from app.services.risk_provider import RiskProvider


class DecisionEngine:
    """
    Deterministic Decision Engine for Sentinel AI Part 3.
    THE LLM MUST NEVER AUTHORIZE AN ACTION.
    The final authorization decision is computed strictly by deterministic Python rules.
    """

    def __init__(self, risk_provider: Optional[RiskProvider] = None, policy_engine: Optional[PolicyEngine] = None):
        self.risk_provider = risk_provider or MockRiskProvider()
        self.policy_engine = policy_engine or PolicyEngine()

    def evaluate_action(
        self,
        action: ProposedAction,
        db: Session,
        risk_override: Optional[RiskResult] = None
    ) -> DecisionObject:
        """
        Executes the deterministic decision pipeline:
        1. Obtain risk score & factors via RiskProvider (or override for testing).
        2. Validate agent identity & permissions (least-privilege).
        3. Evaluate priority-ordered security policies (policies override low risk).
        4. Create approval record if decision is REQUIRE_APPROVAL.
        5. Persist audit trail in DecisionRecord.
        6. Return strictly-typed DecisionObject.
        """
        # Step 1: Obtain risk analysis from RiskProvider (mock or real Part 2)
        risk_result = risk_override if risk_override is not None else self.risk_provider.get_risk(action)

        # Step 2: Check agent existence, active status, and least-privilege tool & operation permissions
        perm_result = check_agent_permission(action, db)

        # Build evaluation context for Policy Engine
        eval_context = {
            "permission_denied": not perm_result.allowed,
            "permission_reason": perm_result.reason
        }

        # Step 3: Run deterministic Policy Engine
        policy_eval = self.policy_engine.evaluate(action, risk_result, eval_context)
        final_decision = policy_eval.decision
        rule_triggered = policy_eval.rule_name if final_decision != DecisionEnum.ALLOW else None
        explanation = policy_eval.explanation

        # Step 4: Handle Human Approval creation if required
        requires_approval = (final_decision == DecisionEnum.REQUIRE_APPROVAL)
        approval_record = None
        approval_id: Optional[UUID] = None

        if requires_approval:
            approval_record = ApprovalService.create_pending_approval(
                db=db,
                request_id=action.request_id,
                action=action,
                risk=risk_result,
                policy_name=rule_triggered
            )
            approval_id = UUID(approval_record.approval_id)

        # Generate unique audit log UUID for Part 4
        audit_log_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        decision_obj = DecisionObject(
            request_id=action.request_id,
            decision=final_decision,
            risk_score=risk_result.risk_score,
            risk_factors=risk_result.risk_factors,
            policy_rule_triggered=rule_triggered,
            explanation=explanation,
            requires_human_approval=requires_approval,
            approval_id=approval_id,
            timestamp=timestamp,
            audit_log_id=audit_log_id
        )

        # Step 5: Save decision record to database for SOC Dashboard telemetry and audit trail
        decision_record = DecisionRecord(
            request_id=str(action.request_id),
            session_id=str(action.session_id),
            agent_id=action.agent_id,
            tool_name=action.tool_name,
            operation=action.operation,
            target_resource=action.target_resource,
            destination=action.destination,
            raw_action=action.model_dump_json_contract(),
            decision=final_decision.value,
            risk_score=risk_result.risk_score,
            risk_factors=risk_result.risk_factors.model_dump(),
            policy_rule_triggered=rule_triggered,
            explanation=explanation,
            requires_human_approval=requires_approval,
            approval_id=str(approval_id) if approval_id else None,
            audit_log_id=str(audit_log_id),
            created_at=timestamp
        )
        db.add(decision_record)
        db.commit()

        return decision_obj
