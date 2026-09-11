import { useCallback, useEffect, useState } from "react";
import { getAuditTimeline } from "../api/executor";
import type { AuditLogRow } from "../types/api";
import type { ActivityEvent } from "../types/api";
import { VERDICT_COLOR, type Verdict } from "../lib/palette";

interface Props {
  liveEvents: ActivityEvent[];
}

function isVerdict(d: string): d is Verdict {
  return d === "ALLOW" || d === "REQUIRE_APPROVAL" || d === "BLOCK";
}

export function IncidentTimeline({ liveEvents }: Props) {
  const [rows, setRows] = useState<AuditLogRow[]>([]);

  const load = useCallback(async () => {
    const timeline = await getAuditTimeline(50);
    setRows(timeline);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Reconcile with the server whenever a decision/execution lands on the
  // live bus — audit rows are updated in place server-side (executed,
  // resolved_at), so a fresh GET is simpler and more correct than trying to
  // hand-patch local state from partial event payloads.
  useEffect(() => {
    if (liveEvents.length > 0) load();
  }, [liveEvents.length, load]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-muted">Incident Timeline</h2>
      <div className="space-y-1.5">
        {rows.length === 0 && <p className="text-sm text-ink-muted">No audit history yet.</p>}
        {rows.map((row) => {
          const color = isVerdict(row.decision) ? VERDICT_COLOR[row.decision] : "var(--color-ink-muted)";
          return (
            <div key={row.audit_log_id} className="border-l-2 py-1 pl-3 text-xs" style={{ borderColor: color }}>
              <div className="flex items-center justify-between text-ink-muted">
                <span className="font-mono">{new Date(row.created_at).toLocaleTimeString()}</span>
                <span className="font-semibold" style={{ color }}>
                  {row.decision}
                </span>
              </div>
              <div className="mt-0.5 flex items-center justify-between">
                <span className="font-mono text-ink">
                  {row.tool_name}.{row.operation}
                </span>
                <span className="text-ink-muted">
                  score {row.risk_score} · {row.executed ? "executed" : "not executed"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
