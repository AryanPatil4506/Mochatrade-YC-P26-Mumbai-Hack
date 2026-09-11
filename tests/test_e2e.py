"""End-to-end tests across the gateway (Parts 2+3) and executor (Part 4)
boundary: capability tokens, the approval workflow, audit logging, and the
compromised-agent token checks. Uses FastAPI's TestClient in-process against
an isolated SQLite file so it doesn't depend on `run_all.sh` being up.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_DB_PATH", str(tmp_path / "test_sentinel.db"))
    from services.executor.audit import store

    store.close_connection()
    yield
    store.close_connection()


@pytest.fixture
def gateway_client():
    from services.gateway.api import app as gateway_app

    with TestClient(gateway_app) as client:
        yield client


@pytest.fixture
def executor_client():
    from services.executor.api import app as executor_app

    with TestClient(executor_app) as client:
        yield client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _benign_action() -> dict:
    return {
        "request_id": str(uuid.uuid4()),
        "agent_id": "crm-assistant-01",
        "session_id": str(uuid.uuid4()),
        "timestamp": _now(),
        "tool_name": "crm",
        "operation": "read",
        "arguments": {"customer_id": "customer_123"},
        "target_resource": "customer_123",
        "destination": None,
        "context": {"user_request": "Look up customer_123's status", "untrusted_content_sources": []},
    }


def test_benign_action_allow_and_execute(gateway_client, executor_client):
    action = _benign_action()

    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    assert decision["decision"] == "ALLOW"
    assert decision["capability_token"]

    result = executor_client.post(
        "/v1/execute", json=action, headers={"X-Capability-Token": decision["capability_token"]}
    ).json()
    assert result["executed"] is True
    assert result["success"] is True

    audit = executor_client.get(f"/v1/audit/{action['request_id']}").json()
    assert audit["executed"] is True
    assert audit["decision"] == "ALLOW"


def test_duplicate_request_id_returns_cached_decision(gateway_client):
    action = _benign_action()
    first = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    second = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    assert first == second


def test_privilege_never_granted_blocks_with_no_token(gateway_client):
    action = _benign_action()
    action["agent_id"] = "totally-unregistered-agent"
    action["tool_name"] = "database"
    action["operation"] = "delete"
    action["arguments"] = {"query": "DELETE FROM customers WHERE id='customer_123';"}
    action["target_resource"] = "customers"

    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    assert decision["decision"] == "BLOCK"
    assert decision["capability_token"] is None


def test_forged_token_rejected_and_never_executes(executor_client):
    action = _benign_action()
    resp = executor_client.post("/v1/execute", json=action, headers={"X-Capability-Token": "not.a.real.token"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["reason"] == "signature_invalid"

    audit = executor_client.get(f"/v1/audit/{action['request_id']}").json()
    assert audit["executed"] is False


def test_replayed_token_rejected_but_original_execution_stays_recorded(gateway_client, executor_client):
    action = _benign_action()
    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    token = decision["capability_token"]

    first = executor_client.post("/v1/execute", json=action, headers={"X-Capability-Token": token})
    assert first.status_code == 200
    assert first.json()["executed"] is True

    replay = executor_client.post("/v1/execute", json=action, headers={"X-Capability-Token": token})
    assert replay.status_code == 403
    assert replay.json()["detail"]["reason"] == "replayed"

    audit = executor_client.get(f"/v1/audit/{action['request_id']}").json()
    assert audit["executed"] is True  # the replay must not erase the earlier real execution


def test_token_args_mismatch_rejected(gateway_client, executor_client):
    action = _benign_action()
    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    token = decision["capability_token"]

    tampered = dict(action)
    tampered["arguments"] = {"customer_id": "customer_456"}
    resp = executor_client.post("/v1/execute", json=tampered, headers={"X-Capability-Token": token})
    assert resp.status_code == 403
    assert resp.json()["detail"]["reason"] == "args_mismatch"


def test_require_approval_flow_approve_then_execute(gateway_client, executor_client):
    action = _benign_action()
    action["agent_id"] = "outreach-bot-01"
    action["tool_name"] = "email"
    action["operation"] = "send"
    action["destination"] = "partner@ourcompany.com"
    action["arguments"] = {
        "recipient": "partner@ourcompany.com",
        "subject": "Q3 report",
        "body": "Account balance $10,000, ssn 123-45-6789",
    }
    action["target_resource"] = "financial_report"

    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    assert decision["decision"] == "REQUIRE_APPROVAL"
    assert decision["capability_token"] is None

    pending = gateway_client.get("/v1/approvals", params={"status": "PENDING"}).json()
    match = [p for p in pending if p["request_id"] == action["request_id"]]
    assert len(match) == 1
    approval_id = match[0]["approval_id"]

    resolved = gateway_client.post(
        f"/v1/approvals/{approval_id}/resolve",
        json={"status": "APPROVED", "approver_id": "human-1", "reason": "looks fine"},
    ).json()
    assert resolved["approval"]["status"] == "APPROVED"
    token = resolved["capability_token"]
    assert token

    execution = executor_client.post("/v1/execute", json=action, headers={"X-Capability-Token": token}).json()
    assert execution["executed"] is True

    # An approval can only be resolved once.
    again = gateway_client.post(
        f"/v1/approvals/{approval_id}/resolve",
        json={"status": "REJECTED", "approver_id": "human-1", "reason": "changed mind"},
    )
    assert again.status_code == 409


def test_rejected_approval_never_yields_a_token(gateway_client):
    action = _benign_action()
    action["agent_id"] = "outreach-bot-01"
    action["tool_name"] = "email"
    action["operation"] = "send"
    action["destination"] = "partner@ourcompany.com"
    action["arguments"] = {
        "recipient": "partner@ourcompany.com",
        "subject": "Q3 report",
        "body": "Account balance $10,000, ssn 123-45-6789",
    }
    action["target_resource"] = "financial_report"

    decision = gateway_client.post("/v1/gateway/evaluate", json=action).json()
    assert decision["decision"] == "REQUIRE_APPROVAL"

    pending = gateway_client.get("/v1/approvals", params={"status": "PENDING"}).json()
    approval_id = [p for p in pending if p["request_id"] == action["request_id"]][0]["approval_id"]

    resolved = gateway_client.post(
        f"/v1/approvals/{approval_id}/resolve",
        json={"status": "REJECTED", "approver_id": "human-1", "reason": "too risky"},
    ).json()
    assert resolved["approval"]["status"] == "REJECTED"
    assert resolved["capability_token"] is None
