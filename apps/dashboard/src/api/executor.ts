import { EXECUTOR_BASE, request } from "./client";
import type { ProposedAction } from "../types/contracts";
import type { AuditLogRow, LabRunResult, LabScenarioMeta, ToolResult } from "../types/api";

export function execute(action: ProposedAction, capabilityToken: string): Promise<ToolResult> {
  return request(EXECUTOR_BASE, "/v1/execute", {
    method: "POST",
    headers: { "X-Capability-Token": capabilityToken },
    body: JSON.stringify(action),
  });
}

export function getAuditTimeline(limit = 50): Promise<AuditLogRow[]> {
  return request(EXECUTOR_BASE, `/v1/audit/timeline?limit=${limit}`);
}

export function getAuditEntry(request_id: string): Promise<AuditLogRow> {
  return request(EXECUTOR_BASE, `/v1/audit/${request_id}`);
}

export function listLabScenarios(): Promise<LabScenarioMeta[]> {
  return request(EXECUTOR_BASE, "/v1/lab/scenarios");
}

export function runLabScenario(scenario_id: string): Promise<LabRunResult> {
  return request(EXECUTOR_BASE, `/v1/lab/run/${scenario_id}`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export const activityStreamUrl = `${EXECUTOR_BASE}/v1/events`;
