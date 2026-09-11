from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.part4.executor.model import DecisionObject, ExecutionResult, ProposedAction
from app.part4.executor.tool_registry import execute_tool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_request(proposed_action: ProposedAction, decision: DecisionObject) -> ExecutionResult:
    """Enforce the Part 3 decision on the original proposed action."""
    if proposed_action is None or decision is None:
        return ExecutionResult(
            request_id="",
            success=False,
            executed=False,
            tool_name="",
            operation="",
            result=None,
            error="Invalid request: missing proposed action or decision",
            executed_at=_now_iso(),
        )

    if proposed_action.request_id != decision.request_id:
        return ExecutionResult(
            request_id=proposed_action.request_id,
            success=False,
            executed=False,
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            result=None,
            error="Execution blocked: request id mismatch between proposed action and decision",
            executed_at=_now_iso(),
        )

    decision_state = (decision.approval_status or "").upper()
    if decision.decision == "BLOCK":
        return ExecutionResult(
            request_id=proposed_action.request_id,
            success=False,
            executed=False,
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            result=None,
            error="Execution blocked by authorization decision",
            executed_at=_now_iso(),
        )

    if decision.decision == "REQUIRE_APPROVAL":
        if decision_state == "APPROVED":
            pass
        else:
            return ExecutionResult(
                request_id=proposed_action.request_id,
                success=False,
                executed=False,
                tool_name=proposed_action.tool_name,
                operation=proposed_action.operation,
                result=None,
                error="Execution blocked: approval is not approved",
                executed_at=_now_iso(),
            )

    try:
        result = execute_tool(
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            arguments=proposed_action.arguments,
            target_resource=proposed_action.target_resource,
            destination=proposed_action.destination,
        )
    except ValueError as exc:
        return ExecutionResult(
            request_id=proposed_action.request_id,
            success=False,
            executed=False,
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            result=None,
            error=f"Tool not allowed: {exc}",
            executed_at=_now_iso(),
        )
    except Exception as exc:  # pragma: no cover - defensive catch for runtime tool failures
        return ExecutionResult(
            request_id=proposed_action.request_id,
            success=False,
            executed=False,
            tool_name=proposed_action.tool_name,
            operation=proposed_action.operation,
            result=None,
            error=f"Tool execution failed: {exc}",
            executed_at=_now_iso(),
        )

    return ExecutionResult(
        request_id=proposed_action.request_id,
        success=bool(result.get("success")) if isinstance(result, dict) else False,
        executed=True,
        tool_name=proposed_action.tool_name,
        operation=proposed_action.operation,
        result=result if isinstance(result, dict) else {"raw": result},
        error=None,
        executed_at=_now_iso(),
    )
