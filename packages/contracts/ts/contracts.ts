// Hand-written mirror of packages/contracts/{enums,schemas}.py.
// TODO: replace with a generated file (pydantic -> JSON Schema -> TS) once
// the generation script exists. Keep in sync manually until then.

export type ToolName = "email" | "database" | "crm" | "ticketing" | "web";

export type Operation = "read" | "write" | "update" | "delete" | "send";

export type DecisionValue = "ALLOW" | "REQUIRE_APPROVAL" | "BLOCK";

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export type TaintSource = "email" | "ticket" | "web_page" | "database_record";

export type DetectorMode = "rules+classifier" | "rules_only";

export interface UntrustedContentSource {
  source: TaintSource;
  content: string;
}

export interface ActionContext {
  user_request: string;
  untrusted_content_sources: UntrustedContentSource[];
}

export interface ProposedAction {
  request_id: string;
  agent_id: string;
  session_id: string;
  timestamp: string;
  tool_name: ToolName;
  operation: Operation;
  arguments: Record<string, unknown>;
  target_resource: string;
  destination: string | null;
  context: ActionContext;
}

export interface RiskFactors {
  tool_sensitivity: number;
  data_sensitivity: number;
  privilege_level: number;
  destination_risk: number;
  reversibility: number;
  injection_signal: number;
  behavioral_anomaly: number;
}

export interface RiskEvidence {
  injection_families: string[];
  detected_entity_types: string[];
  record_count_estimate: number;
  intent_drift: number;
  detector_mode: DetectorMode;
}

export interface RiskAssessment {
  request_id: string;
  risk_factors: RiskFactors;
  risk_score: number;
  escalation_floor_triggered: string | null;
  evidence: RiskEvidence;
  computed_at: string;
  engine_version: string;
}

export interface Decision {
  request_id: string;
  decision: DecisionValue;
  risk_score: number;
  risk_factors: RiskFactors;
  policy_rule_triggered: string | null;
  explanation: string | null;
  requires_human_approval: boolean;
  capability_token: string | null;
  timestamp: string;
  audit_log_id: string;
}

export interface ApprovalRecord {
  approval_id: string;
  request_id: string;
  status: ApprovalStatus;
  approver_id: string | null;
  reason: string | null;
  resolved_at: string | null;
}

export interface AuditLogEntry {
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

export interface TaintEntry {
  entry_id: string;
  source: TaintSource;
  reference: string;
  content: string;
  read_at: string;
  step: number;
}
