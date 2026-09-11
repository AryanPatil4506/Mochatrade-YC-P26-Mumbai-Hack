// Hand-written types for shapes the backend returns that are NOT part of
// the frozen packages/contracts models — plain dicts / dataclasses that
// aren't response_model-typed FastAPI routes. See services/executor/api.py,
// services/gateway/api.py, services/agent/api.py.

import type { ApprovalStatus, Operation, ToolName } from "./contracts";

export interface CreateSessionResponse {
  session_id: string;
  agent_id: string;
}

export interface TaintLedgerEntry {
  entry_id: string;
  source: string;
  reference: string;
  content: string;
  read_at: string;
  step: number;
}

export interface TranscriptEntry {
  role: "user" | "assistant";
  content: string;
}

export interface SessionSnapshot {
  session_id: string;
  agent_id: string;
  transcript: TranscriptEntry[];
  taint_ledger: TaintLedgerEntry[];
}

export interface ToolResult {
  request_id: string;
  executed: boolean;
  success: boolean;
  tool_name: string;
  operation: string;
  result: Record<string, unknown> | null;
  error: string | null;
  executed_at: string;
}

export interface ResolveApprovalResponse {
  approval: import("./contracts").ApprovalRecord;
  capability_token: string | null;
}

// Raw AuditLog.to_dict() shape from services/executor/audit/models.py —
// same field names as the frozen AuditLogEntry contract, but returned as a
// plain dict (no extra="forbid" guarantee) from GET /v1/audit/*.
export interface AuditLogRow {
  audit_log_id: string;
  request_id: string;
  agent_id: string;
  tool_name: string;
  operation: string;
  risk_score: number;
  decision: string;
  approval_id: string | null;
  executed: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface ThresholdBand {
  min: number;
  max: number;
  decision: string;
  ui: "green" | "amber" | "orange" | "red";
  set_policy_rule: boolean;
}

export interface EscalationFloor {
  floor: number;
  rule: string;
}

// Raw dict from services/gateway/decision/policy.py:get_policy_snapshot()
export interface PolicySnapshot {
  weights: Record<keyof import("./contracts").RiskFactors, number>;
  thresholds: ThresholdBand[];
  escalation_floors: EscalationFloor[];
}

export interface LabScenarioMeta {
  id: string;
  name: string;
  category: string;
  description: string;
  expected_decision: string;
}

export interface LabRunResult {
  scenario: string;
  proposed_action: import("./contracts").ProposedAction;
  decision: import("./contracts").Decision;
  execution: ToolResult | null;
  executed: boolean;
}

export interface SimulateCompromiseResult {
  outcome: "denied" | "unexpected" | "executor_unreachable";
  status_code?: number;
  message?: string;
  executor_response?: { detail?: { outcome: string; message: string; reason?: string } };
}

// --- Agent per-session SSE events (services/agent/events.py, fed by
// services/agent/graph/nodes.py — see build_proposal/plan_action/etc.) ---

export type AgentSessionEvent =
  | { type: "user_message"; content: string }
  | { type: "taint_read"; source: string; reference: string }
  | { type: "plan"; function_name: string; arguments: Record<string, unknown> }
  | { type: "proposed_action"; request_id: string; tool_name: ToolName; operation: Operation }
  | { type: "decision"; request_id: string; decision: string; risk_score: number }
  | { type: "tool_result"; result: string | null }
  | { type: "assistant_message"; content: string }
  | { type: "turn_complete" }
  | { type: "session_closed" };

// --- Executor shared activity bus (services/executor/events.py, fed by
// services/gateway/decision/events.py via the /internal/events bridge and
// by services/executor/api.py itself) ---

export type ActivityEvent =
  | {
      type: "decision";
      request_id: string;
      agent_id: string;
      tool_name: string;
      operation: string;
      decision: string;
      risk_score: number;
      policy_rule_triggered: string | null;
      timestamp: string;
    }
  | { type: "execution"; request_id: string; tool_name: string; operation: string; success: boolean }
  | { type: "execution_denied"; request_id: string; reason: string };

export interface ResolveApprovalRequest {
  status: ApprovalStatus;
  approver_id?: string | null;
  reason?: string | null;
}
