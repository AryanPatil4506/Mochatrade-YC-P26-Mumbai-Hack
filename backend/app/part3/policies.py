from typing import Optional, Callable, Dict, Any, List
from app.config import settings
from app.part3.schemas.action import ProposedAction
from app.part3.schemas.decision import DecisionEnum, RiskResult


class PolicyRule:
    def __init__(
        self,
        name: str,
        priority: int,
        decision: DecisionEnum,
        description: str,
        condition: Callable[[ProposedAction, RiskResult, Dict[str, Any]], bool],
        explanation_template: str
    ):
        self.name = name
        self.priority = priority
        self.decision = decision
        self.description = description
        self.condition = condition
        self.explanation_template = explanation_template


def rule_agent_permission_denied(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    # Triggered if permission check failed
    return context.get("permission_denied", False)


def rule_destructive_database_op(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    return action.tool_name == "database" and action.operation == "delete"


def rule_external_sensitive_data(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    is_external = bool(action.destination and not action.destination.endswith("@internal.corp"))
    sensitive_data = risk.risk_factors.data_sensitivity >= 70 or any(
        kw in action.target_resource.lower() for kw in ["user", "customer", "pipeline", "credential", "financial", "secret"]
    )
    return is_external and sensitive_data


def rule_high_risk_action(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    return risk.risk_score >= settings.APPROVAL_THRESHOLD


def rule_medium_risk_action(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    return settings.ALLOW_THRESHOLD <= risk.risk_score < settings.APPROVAL_THRESHOLD


def rule_normal_request(action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> bool:
    return risk.risk_score < settings.ALLOW_THRESHOLD


# Configured policies sorted by priority (descending)
DEFAULT_POLICIES: List[PolicyRule] = [
    PolicyRule(
        name="AGENT_PERMISSION_DENIED",
        priority=100,
        decision=DecisionEnum.BLOCK,
        description="Agent lacks role permission, is deactivated, or requested unauthorized tool/operation.",
        condition=rule_agent_permission_denied,
        explanation_template="Action was blocked because the agent does not have permission to perform this operation."
    ),
    PolicyRule(
        name="HIGH_RISK_ACTION",
        priority=90,
        decision=DecisionEnum.BLOCK,
        description=f"Action risk score exceeds the maximum permitted threshold of {settings.APPROVAL_THRESHOLD}.",
        condition=rule_high_risk_action,
        explanation_template="Action was blocked because the risk score exceeds the maximum permitted threshold."
    ),
    PolicyRule(
        name="EXTERNAL_SENSITIVE_DATA",
        priority=85,
        decision=DecisionEnum.REQUIRE_APPROVAL,
        description="Outbound transmission of sensitive data to an external destination requires human verification.",
        condition=rule_external_sensitive_data,
        explanation_template="Human approval is required because sensitive data is being transmitted to an external destination."
    ),
    PolicyRule(
        name="MEDIUM_RISK_ACTION",
        priority=80,
        decision=DecisionEnum.REQUIRE_APPROVAL,
        description=f"Action risk score is in the medium range ({settings.ALLOW_THRESHOLD}-{settings.APPROVAL_THRESHOLD - 1}) requiring human sign-off.",
        condition=rule_medium_risk_action,
        explanation_template="Human approval is required because the action falls within the medium-risk range."
    ),
    PolicyRule(
        name="DESTRUCTIVE_DATABASE_OPERATION",
        priority=75,
        decision=DecisionEnum.BLOCK,
        description="Destructive database delete operations are blocked by default security posture.",
        condition=rule_destructive_database_op,
        explanation_template="Action was blocked because destructive database operations are restricted by security policy."
    ),
    PolicyRule(
        name="NORMAL_REQUEST",
        priority=10,
        decision=DecisionEnum.ALLOW,
        description=f"Standard low-risk request below {settings.ALLOW_THRESHOLD} executed with valid agent authorization.",
        condition=rule_normal_request,
        explanation_template="Action is permitted because the agent has the required permission and the risk score is below the approval threshold."
    )
]
