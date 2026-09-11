import { useCountUp } from "../hooks/useCountUp";
import { VERDICT_LABEL, colorForScore } from "../lib/palette";
import type { CurrentDecision } from "../lib/currentDecision";

interface Props {
  decision: CurrentDecision | null;
}

export function RiskGauge({ decision }: Props) {
  const score = useCountUp(decision?.risk_score ?? 0);
  const color = decision ? colorForScore(decision.risk_score, decision.decision) : "var(--color-ink-muted)";

  return (
    <div className="flex flex-col items-center gap-1 py-6">
      <div className="text-6xl font-semibold tabular-nums" style={{ color }}>
        {decision ? score : "—"}
      </div>
      <div className="text-sm font-semibold uppercase tracking-wide" style={{ color }}>
        {decision ? VERDICT_LABEL[decision.decision] : "no decision yet"}
      </div>
      {decision?.policy_rule_triggered && (
        <div className="mt-1 font-mono text-xs text-ink-muted">{decision.policy_rule_triggered}</div>
      )}
      {decision && (
        <div className="mt-1 truncate font-mono text-xs text-ink-muted" title={decision.request_id}>
          {decision.request_id.slice(0, 8)} · {decision.source}
        </div>
      )}
    </div>
  );
}
