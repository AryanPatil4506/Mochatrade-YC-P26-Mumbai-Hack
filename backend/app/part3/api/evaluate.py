from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.part3.database.database import get_db
from app.part3.schemas.action import ProposedAction
from app.part3.schemas.decision import DecisionObject, RiskResult, RiskFactors
from app.part3.services.decision_engine import DecisionEngine
from app.part3.services.mock_risk_provider import MockRiskProvider
from app.part3.services.approval_service import ApprovalService


class ExecuteDecisionRequest(BaseModel):
    action: ProposedAction
    decision: DecisionObject

router = APIRouter(prefix="/api/policy", tags=["Policy Evaluation"])

# Primary decision engine instance
decision_engine = DecisionEngine(risk_provider=MockRiskProvider())


@router.post("/evaluate", response_model=DecisionObject)
def evaluate_action_endpoint(
    action: ProposedAction,
    risk_score_override: Optional[int] = Query(None, ge=0, le=100, description="Optional risk score override for developer simulator/test harness"),
    db: Session = Depends(get_db)
) -> DecisionObject:
    """
    Main Part 3 Policy & Decision Gateway.
    Receives ProposedAction from Part 1 / Agent client.
    Evaluates agent least-privilege permissions, policies, and Part 2 risk scores deterministically.
    Returns authoritative DecisionObject.
    """
    risk_override = None
    if risk_score_override is not None:
        risk_override = RiskResult(
            risk_score=risk_score_override,
            risk_factors=RiskFactors(
                tool_sensitivity=min(100, risk_score_override + 5),
                data_sensitivity=risk_score_override,
                privilege_level=max(0, risk_score_override - 10),
                destination_risk=risk_score_override if action.destination else 10,
                reversibility=90 if action.operation == "delete" else 30,
                injection_signal=70 if risk_score_override >= 70 else 10,
                behavioral_anomaly=risk_score_override
            ),
            provider_name="manual_override"
        )

    return decision_engine.evaluate_action(action=action, db=db, risk_override=risk_override)


@router.post("/evaluate-and-execute", response_model=dict)
def evaluate_and_execute_action_endpoint(
    action: ProposedAction,
    risk_score_override: Optional[int] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """Evaluate with Part 3, then enforce and audit through Part 4."""
    decision = evaluate_action_endpoint(action, risk_score_override, db)
    approval_status = None
    if decision.approval_id:
        approval_status = ApprovalService.get_approval(db, decision.approval_id).status

    from app.integration import execute_part3_decision

    return execute_part3_decision(
        action,
        decision,
        approval_status=approval_status,
    )


@router.post("/execute", response_model=dict)
def execute_decision_endpoint(
    payload: ExecuteDecisionRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Execute an existing Part 3 decision after its approval is resolved."""
    if payload.action.request_id != payload.decision.request_id:
        approval_status = None
    elif payload.decision.approval_id:
        approval_status = ApprovalService.get_approval(db, payload.decision.approval_id).status
    else:
        approval_status = None

    from app.integration import execute_part3_decision

    return execute_part3_decision(
        payload.action,
        payload.decision,
        approval_status=approval_status,
    )
