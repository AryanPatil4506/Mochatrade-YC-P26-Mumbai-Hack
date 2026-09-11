import type { RiskFactors } from "../types/contracts";
import type { Verdict } from "./palette";

// Whatever the freshest decision the dashboard has seen is, from any
// source. Only the Action Simulator and Attack Lab flows carry a full
// RiskFactors breakdown (risk_factors is present); a decision surfaced only
// through the agent-session SSE "decision" event has just a score.
export interface CurrentDecision {
  source: "simulator" | "lab" | "session";
  request_id: string;
  decision: Verdict;
  risk_score: number;
  risk_factors: RiskFactors | null;
  policy_rule_triggered?: string | null;
}
