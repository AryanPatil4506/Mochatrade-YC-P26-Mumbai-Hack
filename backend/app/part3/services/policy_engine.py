from typing import List, Dict, Any, Optional
from app.part3.policies import PolicyRule, DEFAULT_POLICIES
from app.part3.schemas.action import ProposedAction
from app.part3.schemas.decision import RiskResult


class PolicyEvaluationResult:
    def __init__(self, rule: PolicyRule, explanation: str):
        self.rule = rule
        self.decision = rule.decision
        self.rule_name = rule.name
        self.priority = rule.priority
        self.explanation = explanation


class PolicyEngine:
    """
    Deterministic Policy Engine.
    Evaluates configured security policies in strict priority order (higher priority first).
    Ensures authorization policies override generic risk scores.
    """

    def __init__(self, policies: Optional[List[PolicyRule]] = None):
        # Sort policies descending by priority
        base = policies if policies is not None else DEFAULT_POLICIES
        self.policies = sorted(base, key=lambda p: p.priority, reverse=True)

    def evaluate(self, action: ProposedAction, risk: RiskResult, context: Dict[str, Any]) -> PolicyEvaluationResult:
        for policy in self.policies:
            if policy.condition(action, risk, context):
                # Format explanation with custom context reason if available
                explanation = policy.explanation_template
                if policy.name == "AGENT_PERMISSION_DENIED" and context.get("permission_reason"):
                    explanation = f"{policy.explanation_template} ({context.get('permission_reason')})"

                return PolicyEvaluationResult(rule=policy, explanation=explanation)

        # Fallback default safe rule if no rules match (should not happen with NORMAL_REQUEST)
        fallback = self.policies[-1]
        return PolicyEvaluationResult(rule=fallback, explanation=fallback.explanation_template)
