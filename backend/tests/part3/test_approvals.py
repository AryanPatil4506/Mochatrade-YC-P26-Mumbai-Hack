from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.part3.models.approval import ApprovalRecord
from app.part3.schemas.approval import ApprovalActionRequest, ApprovalStatus
from app.part3.services.approval_service import ApprovalService


def test_test6_approve_pending_request(db_session):
    """Test 6: Approve pending request -> PENDING to APPROVED"""
    req_id = uuid4()
    rec = ApprovalService.create_pending_approval(db_session, req_id)
    assert rec.status == ApprovalStatus.PENDING.value
    assert rec.resolved_at is None

    payload = ApprovalActionRequest(approver_id="admin_01", reason="Verified request.")
    approved = ApprovalService.approve(db_session, rec.approval_id, payload)

    assert approved.status == ApprovalStatus.APPROVED.value
    assert approved.approver_id == "admin_01"
    assert approved.reason == "Verified request."
    assert approved.resolved_at is not None


def test_test7_reject_pending_request(db_session):
    """Test 7: Reject pending request -> PENDING to REJECTED"""
    req_id = uuid4()
    rec = ApprovalService.create_pending_approval(db_session, req_id)
    assert rec.status == ApprovalStatus.PENDING.value

    payload = ApprovalActionRequest(approver_id="security_lead", reason="Unauthorized request.")
    rejected = ApprovalService.reject(db_session, rec.approval_id, payload)

    assert rejected.status == ApprovalStatus.REJECTED.value
    assert rejected.approver_id == "security_lead"
    assert rejected.reason == "Unauthorized request."
    assert rejected.resolved_at is not None


def test_test8_approve_already_approved_request(db_session):
    """Test 8: Approve already approved request -> ERROR (HTTP 400)"""
    req_id = uuid4()
    rec = ApprovalService.create_pending_approval(db_session, req_id)
    payload = ApprovalActionRequest(approver_id="admin_01", reason="First approval")
    ApprovalService.approve(db_session, rec.approval_id, payload)

    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.approve(db_session, rec.approval_id, payload)
    assert exc_info.value.status_code == 400
    assert "Only PENDING requests can be resolved" in exc_info.value.detail


def test_test9_reject_already_rejected_request(db_session):
    """Test 9: Reject already rejected request -> ERROR (HTTP 400)"""
    req_id = uuid4()
    rec = ApprovalService.create_pending_approval(db_session, req_id)
    payload = ApprovalActionRequest(approver_id="admin_01", reason="First rejection")
    ApprovalService.reject(db_session, rec.approval_id, payload)

    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.reject(db_session, rec.approval_id, payload)
    assert exc_info.value.status_code == 400
    assert "Only PENDING requests can be resolved" in exc_info.value.detail


def test_cannot_approve_rejected_or_reject_approved(db_session):
    """State machine integrity: APPROVED cannot transition to REJECTED, and vice versa"""
    req_id = uuid4()
    rec = ApprovalService.create_pending_approval(db_session, req_id)
    payload = ApprovalActionRequest(approver_id="admin_01", reason="Test")
    ApprovalService.approve(db_session, rec.approval_id, payload)

    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.reject(db_session, rec.approval_id, payload)
    assert exc_info.value.status_code == 400


def test_api_approval_flow(client, make_action):
    """Full HTTP API test of evaluate -> pending approval -> approve endpoint"""
    action = make_action(agent_id="sales_agent", tool_name="email", operation="send")
    payload = action.model_dump_json_contract()

    # Step 1: Evaluate endpoint
    resp = client.post("/api/policy/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "REQUIRE_APPROVAL"
    assert data["requires_human_approval"] is True
    approval_id = data["approval_id"]
    assert approval_id is not None

    # Step 2: Pending approvals endpoint
    pending_resp = client.get("/api/approvals/pending")
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json()
    assert any(p["approval_id"] == approval_id for p in pending_list)

    # Step 3: Approve request via API
    resolve_resp = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"approver_id": "admin_01", "reason": "Verified request."}
    )
    assert resolve_resp.status_code == 200
    res_data = resolve_resp.json()
    assert res_data["status"] == "APPROVED"
    assert res_data["approver_id"] == "admin_01"

    # Step 4: Verify it's no longer in pending
    pending_resp2 = client.get("/api/approvals/pending")
    assert not any(p["approval_id"] == approval_id for p in pending_resp2.json())

    # Step 5: Duplicate approval returns 400
    dup_resp = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"approver_id": "admin_01", "reason": "Second try"}
    )
    assert dup_resp.status_code == 400
