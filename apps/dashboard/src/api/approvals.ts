import { GATEWAY_BASE, request } from "./client";
import type { ApprovalRecord, ApprovalStatus } from "../types/contracts";
import type { ResolveApprovalRequest, ResolveApprovalResponse } from "../types/api";

export function listApprovals(status?: ApprovalStatus): Promise<ApprovalRecord[]> {
  const qs = status ? `?status=${status}` : "";
  return request(GATEWAY_BASE, `/v1/approvals${qs}`);
}

export function resolveApproval(
  approval_id: string,
  body: ResolveApprovalRequest,
): Promise<ResolveApprovalResponse> {
  return request(GATEWAY_BASE, `/v1/approvals/${approval_id}/resolve`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
