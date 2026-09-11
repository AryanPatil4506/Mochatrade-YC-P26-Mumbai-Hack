import { useCountUp } from "../hooks/useCountUp";
import { VERDICT_LABEL, colorForScore } from "../lib/palette";
import type { CurrentDecision } from "../lib/currentDecision";
import { Badge } from "./Badge";

interface Props {
  decision: CurrentDecision | null;
}

export function RiskGauge({ decision }: Props) {
  const score = useCountUp(decision?.risk_score ?? 0);
  const color = decision ? colorForScore(decision.risk_score, decision.decision) : "var(--color-ink-muted)";

  return (
    <div className="sentinel-card m-4 mb-3 p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
          Overall Risk Score
        </span>
        {decision && <Badge color={color}>{VERDICT_LABEL[decision.decision]}</Badge>}
      </div>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="text-5xl font-bold tabular-nums" style={{ color }}>
          {decision ? score : "—"}
        </span>
        <span className="text-sm font-medium text-ink-muted">/ 100</span>
      </div>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-raised">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${decision?.risk_score ?? 0}%`, background: color }}
        />
      </div>

      {decision?.policy_rule_triggered && (
        <div className="mt-3 font-mono text-[11px] text-ink-muted">{decision.policy_rule_triggered}</div>
      )}
      {decision && (
        <div className="mt-1 truncate font-mono text-[11px] text-ink-muted/70" title={decision.request_id}>
          {decision.request_id.slice(0, 8)} · {decision.source}
        </div>
      )}
      {!decision && <p className="mt-3 text-sm text-ink-muted">No decision yet.</p>}
    </div>
  );
}
