from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from app.part4.audit.service import AuditService
from app.part4.executor.executor import execute_request
from app.part4.executor.model import DecisionObject, ProposedAction


def execute_part3_decision(
    proposed_action: Any,
    decision: Any,
    *,
    approval_status: Optional[str] = None,
) -> dict[str, Any]:
    """Adapt Part 3 models to Part 4, enforce, and persist the full lifecycle."""
    action_data = proposed_action.model_dump(mode="json") if hasattr(proposed_action, "model_dump") else asdict(proposed_action)
    decision_data = decision.model_dump(mode="json") if hasattr(decision, "model_dump") else asdict(decision)
    decision_data["decision"] = getattr(decision_data["decision"], "value", decision_data["decision"])
    decision_data["approval_status"] = approval_status

    action = ProposedAction(**action_data)
    authorization = DecisionObject(**decision_data)
    execution = execute_request(action, authorization)

    existing_audit = AuditService.get_log(authorization.audit_log_id) if authorization.audit_log_id else None
    if existing_audit:
        AuditService.update_resolution(
            existing_audit.audit_log_id,
            executed=execution.executed,
            resolved_at=execution.executed_at if execution.executed else None,
        )
        audit_log = AuditService.get_log(existing_audit.audit_log_id)
    else:
        audit_log = AuditService.create_log(
            proposed_action=action,
            decision=authorization,
            executed=execution.executed,
            resolved_at=execution.executed_at if execution.executed else None,
        )
    AuditService.record_execution(request_id=action.request_id, execution_result=execution)

    return {
        "decision": decision_data,
        "execution": asdict(execution),
        "audit": audit_log.to_dict(),
    }