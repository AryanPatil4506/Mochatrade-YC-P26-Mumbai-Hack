import pytest
from pydantic import ValidationError
from app.schemas.decision import DecisionEnum, RiskResult, RiskFactors
from app.services.decision_engine import DecisionEngine
from app.services.mock_risk_provider import MockRiskProvider


def test_test1_authorized_low_risk(db_session, make_action):
    """Test 1: Authorized + low risk -> ALLOW"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    action = make_action(agent_id="support_agent", tool_name="crm", operation="read")
    low_risk = RiskResult(risk_score=20, risk_factors=RiskFactors(tool_sensitivity=20, data_sensitivity=10))

    decision = engine.evaluate_action(action, db_session, risk_override=low_risk)
    assert decision.decision == DecisionEnum.ALLOW
    assert decision.requires_human_approval is False
    assert decision.approval_id is None
    assert decision.risk_score == 20
    assert "permitted" in decision.explanation.lower()


def test_test2_authorized_medium_risk(db_session, make_action):
    """Test 2: Authorized + medium risk -> REQUIRE_APPROVAL"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    action = make_action(agent_id="sales_agent", tool_name="email", operation="send")
    med_risk = RiskResult(risk_score=70, risk_factors=RiskFactors(tool_sensitivity=60, data_sensitivity=70))

    decision = engine.evaluate_action(action, db_session, risk_override=med_risk)
    assert decision.decision == DecisionEnum.REQUIRE_APPROVAL
    assert decision.requires_human_approval is True
    assert decision.approval_id is not None
    assert decision.policy_rule_triggered == "MEDIUM_RISK_ACTION"


def test_test3_authorized_high_risk(db_session, make_action):
    """Test 3: Authorized + high risk -> BLOCK"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    # admin_agent has database.write permission, but risk is 90
    action = make_action(agent_id="admin_agent", tool_name="database", operation="write")
    high_risk = RiskResult(risk_score=90, risk_factors=RiskFactors(tool_sensitivity=90, data_sensitivity=90))

    decision = engine.evaluate_action(action, db_session, risk_override=high_risk)
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.requires_human_approval is False
    assert decision.approval_id is None
    assert decision.policy_rule_triggered == "HIGH_RISK_ACTION"


def test_test4_unauthorized_tool(db_session, make_action):
    """Test 4: Unauthorized tool -> BLOCK (Policy overrides low risk)"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    # support_agent has NO database tool permission
    action = make_action(agent_id="support_agent", tool_name="database", operation="read")
    low_risk = RiskResult(risk_score=10, risk_factors=RiskFactors())

    decision = engine.evaluate_action(action, db_session, risk_override=low_risk)
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.policy_rule_triggered == "AGENT_PERMISSION_DENIED"


def test_test5_unauthorized_operation(db_session, make_action):
    """Test 5: Unauthorized operation -> BLOCK"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    # sales_agent has ticketing.read but not ticketing.update
    action = make_action(agent_id="sales_agent", tool_name="ticketing", operation="update")
    low_risk = RiskResult(risk_score=15, risk_factors=RiskFactors())

    decision = engine.evaluate_action(action, db_session, risk_override=low_risk)
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.policy_rule_triggered == "AGENT_PERMISSION_DENIED"


def test_test10_invalid_risk_score_above_100():
    """Test 10: Invalid risk score 101 -> validation error"""
    with pytest.raises(ValidationError):
        RiskResult(risk_score=101, risk_factors=RiskFactors())


def test_test11_negative_risk_score():
    """Test 11: Negative risk score -1 -> validation error"""
    with pytest.raises(ValidationError):
        RiskResult(risk_score=-1, risk_factors=RiskFactors())


def test_test12_missing_agent(db_session, make_action):
    """Test 12: Missing agent -> BLOCK"""
    engine = DecisionEngine(risk_provider=MockRiskProvider())
    action = make_action(agent_id="phantom_agent", tool_name="crm", operation="read")
    low_risk = RiskResult(risk_score=5, risk_factors=RiskFactors())

    decision = engine.evaluate_action(action, db_session, risk_override=low_risk)
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.policy_rule_triggered == "AGENT_PERMISSION_DENIED"
    assert "does not exist" in decision.explanation
