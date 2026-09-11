import type { RiskFactors } from "../types/contracts";
import type { PolicySnapshot } from "../types/api";
import type { CurrentDecision } from "../lib/currentDecision";

interface Props {
  decision: CurrentDecision | null;
  policy: PolicySnapshot | null;
}

const FACTOR_LABEL: Record<keyof RiskFactors, string> = {
  tool_sensitivity: "Tool sensitivity",
  data_sensitivity: "Data sensitivity",
  privilege_level: "Privilege level",
  destination_risk: "Destination risk",
  reversibility: "Reversibility",
  injection_signal: "Injection signal",
  behavioral_anomaly: "Behavioral anomaly",
};

export function FactorBars({ decision, policy }: Props) {
  if (!decision) {
    return <p className="px-4 py-6 text-sm text-ink-muted">Run an action to see its risk breakdown.</p>;
  }

  if (!decision.risk_factors) {
    return (
      <p className="px-4 py-6 text-sm text-ink-muted">
        Factor breakdown unavailable — this decision came from the agent chat's live event stream, which only
        carries the composite score. Run the same action via the Action Simulator or Attack Lab below to see the
        full 7-factor breakdown.
      </p>
    );
  }

  const weights = policy?.weights;
  const entries = (Object.keys(decision.risk_factors) as (keyof RiskFactors)[])
    .map((key) => {
      const value = decision.risk_factors![key];
      const weight = weights?.[key] ?? 0;
      return { key, value, weighted: value * weight };
    })
    .sort((a, b) => b.weighted - a.weighted);

  return (
    <div className="space-y-2 p-4">
      {entries.map(({ key, value, weighted }) => (
        <div key={key}>
          <div className="mb-0.5 flex justify-between text-xs text-ink-muted">
            <span>{FACTOR_LABEL[key]}</span>
            <span className="font-mono">
              {value}
              {weights && <span className="text-ink-muted/60"> · w {weighted.toFixed(1)}</span>}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded bg-surface">
            <div className="h-full rounded bg-approval" style={{ width: `${value}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
