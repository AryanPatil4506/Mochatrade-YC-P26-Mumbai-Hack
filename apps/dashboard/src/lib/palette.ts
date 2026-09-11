// Central mapping from decision/ui values to the fixed semantic palette.
// Color carries meaning only, never decorative — see CLAUDE.md.

export type Verdict = "ALLOW" | "REQUIRE_APPROVAL" | "BLOCK";

export const VERDICT_COLOR: Record<Verdict, string> = {
  ALLOW: "var(--color-allow)",
  REQUIRE_APPROVAL: "var(--color-approval)",
  BLOCK: "var(--color-block)",
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  ALLOW: "ALLOW",
  REQUIRE_APPROVAL: "REQUIRE APPROVAL",
  BLOCK: "BLOCK",
};

// GET /v1/policy's thresholds[].ui band hint: green/amber/orange/red. Amber
// is an ALLOW with a policy_rule_triggered set (elevated but not escalated) —
// visually distinct from a clean green ALLOW.
export function colorForScore(score: number, decision: Verdict): string {
  if (decision === "BLOCK") return VERDICT_COLOR.BLOCK;
  if (decision === "REQUIRE_APPROVAL") return VERDICT_COLOR.REQUIRE_APPROVAL;
  return score >= 30 ? "var(--color-flagged)" : VERDICT_COLOR.ALLOW;
}
