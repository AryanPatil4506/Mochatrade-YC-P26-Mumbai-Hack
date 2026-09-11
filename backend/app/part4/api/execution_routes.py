from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.part4.audit.service import AuditService
from app.part4.executor.model import DecisionObject, ProposedAction
from app.integration import execute_part3_decision


class ExecutionRequest(BaseModel):
    proposed_action: ProposedAction
    decision: DecisionObject
    approval_status: Optional[str] = Field(default=None)


execution_router = APIRouter(prefix="/part4", tags=["Execution"])


@execution_router.post("/execute", response_model=Dict[str, Any])
def execute_part3_request(payload: ExecutionRequest) -> Dict[str, Any]:
    return execute_part3_decision(
        payload.proposed_action,
        payload.decision,
        approval_status=payload.approval_status,
    )


@execution_router.get("/audit/{request_id}", response_model=Dict[str, Any])
def get_request_audit(request_id: str) -> Dict[str, Any]:
    log = AuditService.get_log_by_request(request_id)
    return log.to_dict() if log else {"request_id": request_id, "audit": None}
