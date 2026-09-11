from typing import Optional
from app.schemas.action import ProposedAction
from app.schemas.decision import RiskResult, RiskFactors
from app.services.risk_provider import RiskProvider


class MockRiskProvider(RiskProvider):
    """
    Mock implementation of Part 2 Risk Provider.
    Implements standard predefined benchmark scenarios and intelligent deterministic
    mock factor calculations for arbitrary dynamic test inputs.
    """

    def __init__(self, override_score: Optional[int] = None, override_factors: Optional[RiskFactors] = None):
        self.override_score = override_score
        self.override_factors = override_factors

    def get_risk(self, action: ProposedAction) -> RiskResult:
        # If explicit override is configured (useful in test harnesses)
        if self.override_score is not None:
            return RiskResult(
                risk_score=self.override_score,
                risk_factors=self.override_factors or RiskFactors(
                    tool_sensitivity=self.override_score,
                    data_sensitivity=self.override_score,
                    privilege_level=self.override_score,
                    destination_risk=self.override_score,
                    reversibility=self.override_score,
                    injection_signal=0,
                    behavioral_anomaly=0
                ),
                provider_name="mock_risk_provider_override"
            )

        # Predefined Scenario 4: Unauthorized tool check with low risk
        # Note: Demonstrates that security policy overrides a low risk score!
        if str(action.request_id) == "44444444-4444-4444-8444-444444444444" or (
            action.tool_name == "database" and action.operation == "delete" and action.arguments.get("table") == "temp_cache"
        ):
            return RiskResult(
                risk_score=20,
                risk_factors=RiskFactors(
                    tool_sensitivity=20,
                    data_sensitivity=20,
                    privilege_level=20,
                    destination_risk=10,
                    reversibility=20,
                    injection_signal=0,
                    behavioral_anomaly=10
                ),
                provider_name="mock_risk_provider"
            )

        # Predefined Scenario 1: Safe
        # agent_id: support_agent, tool_name: crm, operation: read -> risk_score: 20
        if action.tool_name == "crm" and action.operation == "read":
            return RiskResult(
                risk_score=20,
                risk_factors=RiskFactors(
                    tool_sensitivity=20,
                    data_sensitivity=10,
                    privilege_level=20,
                    destination_risk=10,
                    reversibility=10,
                    injection_signal=0,
                    behavioral_anomaly=10
                ),
                provider_name="mock_risk_provider"
            )

        # Predefined Scenario 2: Medium risk
        # agent_id: sales_agent, tool_name: email, operation: send -> risk_score: 70
        if action.tool_name == "email" and action.operation == "send":
            # Check destination or external factors
            return RiskResult(
                risk_score=70,
                risk_factors=RiskFactors(
                    tool_sensitivity=60,
                    data_sensitivity=75,
                    privilege_level=60,
                    destination_risk=80,
                    reversibility=40,
                    injection_signal=70,
                    behavioral_anomaly=50
                ),
                provider_name="mock_risk_provider"
            )

        # Predefined Scenario 3: High risk
        # agent_id: support_agent, tool_name: database, operation: delete -> risk_score: 90
        if action.tool_name == "database" and action.operation == "delete":
            return RiskResult(
                risk_score=90,
                risk_factors=RiskFactors(
                    tool_sensitivity=90,
                    data_sensitivity=90,
                    privilege_level=85,
                    destination_risk=95,
                    reversibility=95,
                    injection_signal=80,
                    behavioral_anomaly=90
                ),
                provider_name="mock_risk_provider"
            )

        # Generic heuristics for any dynamic actions submitted via simulator or api
        tool_sens = 50
        if action.tool_name in {"database"}:
            tool_sens = 85
        elif action.tool_name in {"email", "ticketing"}:
            tool_sens = 60
        elif action.tool_name in {"crm", "web"}:
            tool_sens = 35

        reversibility = 50
        if action.operation in {"delete"}:
            reversibility = 90
        elif action.operation in {"write", "send"}:
            reversibility = 65
        elif action.operation in {"read"}:
            reversibility = 10

        dest_risk = 80 if action.destination else 20
        privilege = 75 if action.agent_id == "admin_agent" else 40

        # Untrusted injection check
        has_suspicious_text = False
        if action.context and action.context.untrusted_content_sources:
            for src in action.context.untrusted_content_sources:
                if any(kw in src.content.lower() for kw in ["ignore", "drop", "admin", "bypass", "leak"]):
                    has_suspicious_text = True
        injection_signal = 80 if has_suspicious_text else 15

        calculated_score = min(100, max(0, int((tool_sens * 0.3) + (reversibility * 0.3) + (dest_risk * 0.2) + (injection_signal * 0.2))))

        return RiskResult(
            risk_score=calculated_score,
            risk_factors=RiskFactors(
                tool_sensitivity=tool_sens,
                data_sensitivity=tool_sens,
                privilege_level=privilege,
                destination_risk=dest_risk,
                reversibility=reversibility,
                injection_signal=injection_signal,
                behavioral_anomaly=30
            ),
            provider_name="mock_risk_provider"
        )
