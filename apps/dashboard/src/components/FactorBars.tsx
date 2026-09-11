import { Gauge } from "lucide-react";
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
  return (
    <div className="sentinel-card m-4 mt-0 p-4">
      <h3 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
        <Gauge size={13} className="text-brand" />
        Risk Analysis
      </h3>

      {!decision && <p className="mt-3 text-sm text-ink-muted">Run an action to see its risk breakdown.</p>}

      {decision && !decision.risk_factors && (
        <p className="mt-3 text-sm text-ink-muted">
          Factor breakdown unavailable — this decision came from the agent chat's live event stream, which only
          carries the composite score. Run the same action via the Action Simulator or Attack Lab below to see the
          full 7-factor breakdown.
        </p>
      )}

      {decision?.risk_factors && (
        <FactorList factors={decision.risk_factors} weights={policy?.weights} />
      )}
    </div>
  );
}

function FactorList({
  factors,
  weights,
}: {
  factors: RiskFactors;
  weights?: PolicySnapshot["weights"];
}) {
  const entries = (Object.keys(factors) as (keyof RiskFactors)[])
    .map((key) => {
      const value = factors[key];
      const weight = weights?.[key] ?? 0;
      return { key, value, weighted: value * weight };
    })
    .sort((a, b) => b.weighted - a.weighted);

  return (
    <div className="mt-3 space-y-3">
      {entries.map(({ key, value, weighted }) => (
        <div key={key}>
          <div className="mb-1 flex justify-between text-xs text-ink-muted">
            <span>{FACTOR_LABEL[key]}</span>
            <span className="font-mono text-ink">
              {value}
              {weights && <span className="text-ink-muted/60"> · w {weighted.toFixed(1)}</span>}
            </span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-surface-raised">
            <div className="h-full rounded-full bg-brand" style={{ width: `${value}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
