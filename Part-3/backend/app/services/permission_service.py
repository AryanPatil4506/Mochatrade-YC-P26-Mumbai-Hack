from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent, Permission
from app.schemas.action import ProposedAction


class PermissionCheckResult:
    def __init__(self, allowed: bool, reason: Optional[str] = None, rule: Optional[str] = None):
        self.allowed = allowed
        self.reason = reason
        self.rule = rule


def check_agent_permission(action: ProposedAction, db: Session) -> PermissionCheckResult:
    """
    Validates least-privilege for an agent action against the persistent Agent Registry:
    1. Does agent exist?
    2. Is agent active?
    3. Is tool allowed?
    4. Is operation allowed for that tool?

    If any answer is NO:
    Returns allowed=False, rule="AGENT_PERMISSION_DENIED"
    """
    # 1. Does agent exist?
    agent = db.query(Agent).filter(Agent.agent_id == action.agent_id).first()
    if not agent:
        return PermissionCheckResult(
            allowed=False,
            reason=f"Agent '{action.agent_id}' does not exist in the security registry.",
            rule="AGENT_PERMISSION_DENIED"
        )

    # 2. Is agent active?
    if not agent.is_active:
        return PermissionCheckResult(
            allowed=False,
            reason=f"Agent '{action.agent_id}' is currently deactivated or suspended.",
            rule="AGENT_PERMISSION_DENIED"
        )

    # 3 & 4. Is tool and operation allowed for that agent?
    permission = db.query(Permission).filter(
        Permission.agent_id == action.agent_id,
        Permission.tool_name == action.tool_name,
        Permission.operation == action.operation
    ).first()

    if not permission:
        return PermissionCheckResult(
            allowed=False,
            reason=f"Agent '{action.agent_id}' does not have permission for '{action.tool_name}.{action.operation}'.",
            rule="AGENT_PERMISSION_DENIED"
        )

    return PermissionCheckResult(allowed=True)
