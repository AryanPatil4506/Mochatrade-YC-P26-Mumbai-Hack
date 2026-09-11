from app.part3.policies import DEFAULT_POLICIES
from app.part3.schemas.decision import DecisionEnum, RiskResult, RiskFactors
from app.part3.services.policy_engine import PolicyEngine


def test_policy_priorities_sorted():
    engine = PolicyEngine()
    priorities = [p.priority for p in engine.policies]
    assert priorities == sorted(priorities, reverse=True)
    assert priorities[0] == 100
    assert priorities[-1] == 10


def test_permission_denied_overrides_low_risk(make_action):
    engine = PolicyEngine()
    action = make_action(agent_id="support_agent", tool_name="database", operation="delete")
    low_risk = RiskResult(risk_score=15, risk_factors=RiskFactors(data_sensitivity=10))
    context = {"permission_denied": True, "permission_reason": "Tool not permitted"}

    result = engine.evaluate(action, low_risk, context)
    assert result.decision == DecisionEnum.BLOCK
    assert result.rule_name == "AGENT_PERMISSION_DENIED"
    assert result.priority == 100


def test_high_risk_policy_blocks(make_action):
    engine = PolicyEngine()
    action = make_action(agent_id="support_agent", tool_name="crm", operation="read")
    high_risk = RiskResult(risk_score=95, risk_factors=RiskFactors(data_sensitivity=90))
    context = {"permission_denied": False}

    result = engine.evaluate(action, high_risk, context)
    assert result.decision == DecisionEnum.BLOCK
    assert result.rule_name == "HIGH_RISK_ACTION"


def test_external_sensitive_data_requires_approval(make_action):
    engine = PolicyEngine()
    action = make_action(
        agent_id="sales_agent",
        tool_name="email",
        operation="send",
        target_resource="financial_export",
        destination="external_partner@example.com"
    )
    # Score 50 normally ALLOW, but external + sensitive -> REQUIRE_APPROVAL (Priority 85)
    medium_risk = RiskResult(risk_score=50, risk_factors=RiskFactors(data_sensitivity=85))
    context = {"permission_denied": False}

    result = engine.evaluate(action, medium_risk, context)
    assert result.decision == DecisionEnum.REQUIRE_APPROVAL
    assert result.rule_name == "EXTERNAL_SENSITIVE_DATA"


def test_medium_risk_requires_approval(make_action):
    engine = PolicyEngine()
    action = make_action(agent_id="sales_agent", tool_name="email", operation="send")
    medium_risk = RiskResult(risk_score=70, risk_factors=RiskFactors(tool_sensitivity=60))
    context = {"permission_denied": False}

    result = engine.evaluate(action, medium_risk, context)
    assert result.decision == DecisionEnum.REQUIRE_APPROVAL
    assert result.rule_name == "MEDIUM_RISK_ACTION"


def test_destructive_database_op_blocks(make_action):
    engine = PolicyEngine()
    action = make_action(agent_id="admin_agent", tool_name="database", operation="delete")
    safe_risk = RiskResult(risk_score=40, risk_factors=RiskFactors())
    context = {"permission_denied": False}

    result = engine.evaluate(action, safe_risk, context)
    assert result.decision == DecisionEnum.BLOCK
    assert result.rule_name == "DESTRUCTIVE_DATABASE_OPERATION"
