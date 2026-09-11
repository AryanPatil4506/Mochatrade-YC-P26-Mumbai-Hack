import { GATEWAY_BASE, request } from "./client";
import type { Decision, ProposedAction } from "../types/contracts";
import type { PolicySnapshot } from "../types/api";

export function evaluateAction(action: ProposedAction): Promise<Decision> {
  return request(GATEWAY_BASE, "/v1/gateway/evaluate", {
    method: "POST",
    body: JSON.stringify(action),
  });
}

export function getPolicy(): Promise<PolicySnapshot> {
  return request(GATEWAY_BASE, "/v1/policy");
}
