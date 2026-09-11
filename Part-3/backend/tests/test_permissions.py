from app.services.permission_service import check_agent_permission
from app.models.agent import Agent


def test_valid_agent_permission(db_session, make_action):
    # support_agent has crm.read
    action = make_action(agent_id="support_agent", tool_name="crm", operation="read")
    result = check_agent_permission(action, db_session)
    assert result.allowed is True
    assert result.rule is None


def test_unauthorized_tool(db_session, make_action):
    # support_agent does not have database tool
    action = make_action(agent_id="support_agent", tool_name="database", operation="read")
    result = check_agent_permission(action, db_session)
    assert result.allowed is False
    assert result.rule == "AGENT_PERMISSION_DENIED"


def test_unauthorized_operation(db_session, make_action):
    # sales_agent has ticketing.read but not ticketing.update
    action = make_action(agent_id="sales_agent", tool_name="ticketing", operation="update")
    result = check_agent_permission(action, db_session)
    assert result.allowed is False
    assert result.rule == "AGENT_PERMISSION_DENIED"


def test_missing_agent(db_session, make_action):
    # non-existent agent
    action = make_action(agent_id="rogue_bot", tool_name="crm", operation="read")
    result = check_agent_permission(action, db_session)
    assert result.allowed is False
    assert result.rule == "AGENT_PERMISSION_DENIED"
    assert "does not exist" in result.reason


def test_deactivated_agent(db_session, make_action):
    # Deactivate support_agent
    agent = db_session.query(Agent).filter(Agent.agent_id == "support_agent").first()
    agent.is_active = False
    db_session.commit()

    action = make_action(agent_id="support_agent", tool_name="crm", operation="read")
    result = check_agent_permission(action, db_session)
    assert result.allowed is False
    assert result.rule == "AGENT_PERMISSION_DENIED"
    assert "deactivated" in result.reason
