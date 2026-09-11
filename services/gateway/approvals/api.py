"""GET /v1/approvals, POST /v1/approvals/{id}/resolve."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from packages.contracts.enums import ApprovalStatus
from packages.contracts.schemas import ApprovalRecord
from services.gateway.approvals import queue

router = APIRouter()


class ResolveApprovalRequest(BaseModel):
    status: ApprovalStatus
    approver_id: str | None = None
    reason: str | None = None


class ResolveApprovalResponse(BaseModel):
    """ApprovalRecord (extra=forbid, frozen) has no room for a token field,
    but the endpoint spec explicitly returns "ApprovalRecord (+token
    on APPROVED)" — so this wraps the frozen record rather than extending it."""

    approval: ApprovalRecord
    capability_token: str | None = None


@router.get("/v1/approvals", response_model=list[ApprovalRecord])
async def list_approvals(status: Optional[ApprovalStatus] = Query(None)) -> list[ApprovalRecord]:
    return queue.list_approvals(status=status)


@router.post("/v1/approvals/{approval_id}/resolve", response_model=ResolveApprovalResponse)
async def resolve_approval(approval_id: UUID, body: ResolveApprovalRequest) -> ResolveApprovalResponse:
    if body.status == ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="status must be APPROVED or REJECTED")

    try:
        record, token = queue.resolve_approval(
            approval_id, status=body.status, approver_id=body.approver_id, reason=body.reason
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="approval not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return ResolveApprovalResponse(approval=record, capability_token=token)
