from executor.tool_registry import execute_tool, get_tool
from tools.crm import crm_execute, reset_demo_data
from tools.database import database_execute, reset_sandbox
from tools.email import email_execute, reset_demo_data as reset_email_data
from tools.ticketing import ticketing_execute


def setup_function():
	reset_demo_data()
	reset_email_data()
	reset_sandbox()


def test_registry_exposes_required_sandbox_tools():
	for name in ("crm", "ticketing", "email", "database"):
		assert get_tool(name) is not None


def test_crm_crud_uses_demo_data():
	assert crm_execute("read", target_resource="customer_123")["result"]["customer"]["status"] == "active"
	created = crm_execute("write", {"customer_id": "customer_new", "name": "New Demo"})
	assert created["success"] is True
	updated = crm_execute("update", {"status": "verified"}, target_resource="customer_new")
	assert updated["result"]["customer"]["status"] == "verified"
	assert crm_execute("delete", target_resource="customer_new")["success"] is True


def test_ticketing_validates_missing_ticket():
	result = ticketing_execute("update", {"status": "closed"}, target_resource="missing")
	assert result["success"] is False
	assert "not found" in result["error"].lower()
	assert ticketing_execute("read", [])["success"] is False


def test_email_is_simulated_and_readable():
	sent = email_execute("send", {"subject": "Demo", "body": "Hello"}, destination="demo@example.test")
	assert sent["success"] is True
	assert sent["simulated"] is True
	message_id = sent["result"]["email"]["message_id"]
	assert email_execute("read", target_resource=message_id)["result"]["email"]["body"] == "Hello"


def test_database_uses_isolated_sandbox_and_structured_rows():
	selected = database_execute("select", {"query": "SELECT * FROM customers"})
	assert selected["success"] is True
	assert selected["result"]["rows"][0]["id"] == "customer_123"
	deleted = database_execute("delete", {"query": "DELETE FROM trades"})
	assert deleted["success"] is True
	assert database_execute("select", {"query": "SELECT * FROM trades"})["result"]["rows"] == []


def test_database_rejects_ddl_and_malformed_input():
	dropped = database_execute("delete", {"query": "DROP TABLE trades"})
	malformed = database_execute("select", {"query": "UPDATE customers SET status = 'x'"})
	assert dropped["success"] is False
	assert malformed["success"] is False


def test_registry_executes_tools_with_common_interface():
	result = execute_tool("email", "send", {"subject": "Demo", "body": "Text"}, destination="a@example.test")
	assert result["tool"] == "email"
	assert result["success"] is True
