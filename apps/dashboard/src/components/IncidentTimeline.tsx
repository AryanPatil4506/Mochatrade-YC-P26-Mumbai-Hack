import { useCallback, useEffect, useState } from "react";
import { Check, Copy, History } from "lucide-react";
import { getAuditTimeline } from "../api/executor";
import type { AuditLogRow } from "../types/api";
import type { ActivityEvent } from "../types/api";
import { VERDICT_COLOR, type Verdict } from "../lib/palette";
import { Badge } from "./Badge";

interface Props {
  liveEvents: ActivityEvent[];
}

function isVerdict(d: string): d is Verdict {
  return d === "ALLOW" || d === "REQUIRE_APPROVAL" || d === "BLOCK";
}

function Field({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="shrink-0 text-ink-muted">{label}</span>
      <span className="truncate text-right text-ink" title={note ? `${value} — ${note}` : value}>
        {value}
        {note && <span className="ml-1.5 font-sans italic text-ink-muted">({note})</span>}
      </span>
    </div>
  );
}

export function IncidentTimeline({ liveEvents }: Props) {
  const [rows, setRows] = useState<AuditLogRow[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyRaw = useCallback(async (row: AuditLogRow) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(row, null, 2));
      setCopiedId(row.audit_log_id);
      setTimeout(() => setCopiedId((id) => (id === row.audit_log_id ? null : id)), 1500);
    } catch {
      // Clipboard API can be unavailable (permissions, non-HTTPS context) —
      // this is a nice-to-have for the demo, not something to surface as an error.
    }
  }, []);

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
      <h2 className="mb-3 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
        <History size={13} className="text-brand" />
        Incident Timeline
      </h2>
      <div className="space-y-2">
        {rows.length === 0 && <p className="text-sm text-ink-muted">No audit history yet.</p>}
        {rows.map((row) => {
          const color = isVerdict(row.decision) ? VERDICT_COLOR[row.decision] : "var(--color-ink-muted)";
          const isOpen = expanded === row.audit_log_id;
          return (
            <div
              key={row.audit_log_id}
              className="rounded-lg border-l-2 bg-surface px-3 py-2 text-xs"
              style={{ borderColor: color }}
            >
              <button
                type="button"
                className="w-full cursor-pointer text-left"
                onClick={() => setExpanded(isOpen ? null : row.audit_log_id)}
                aria-expanded={isOpen}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-ink-muted">{new Date(row.created_at).toLocaleTimeString()}</span>
                  <Badge color={color}>{row.decision}</Badge>
                </div>
                <div className="mt-1.5 flex items-center justify-between">
                  <span className="font-mono text-ink">
                    {row.tool_name}.{row.operation}
                  </span>
                  <span className="text-ink-muted">
                    score {row.risk_score} · {row.executed ? "executed" : "not executed"}
                  </span>
                </div>
              </button>
              {isOpen && (
                <div className="mt-2 space-y-1 rounded-md border border-border bg-ground/40 px-2.5 py-2 font-mono text-[11px]">
                  <div className="mb-1.5 flex items-center justify-between">
                    <p className="font-sans text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-muted">
                      Raw audit_logs row
                    </p>
                    <button
                      type="button"
                      className="flex cursor-pointer items-center gap-1 font-sans text-[10px] font-medium text-ink-muted hover:text-ink"
                      onClick={() => copyRaw(row)}
                    >
                      {copiedId === row.audit_log_id ? (
                        <>
                          <Check size={11} className="text-brand" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy size={11} />
                          Copy JSON
                        </>
                      )}
                    </button>
                  </div>
                  <Field label="audit_log_id" value={row.audit_log_id} />
                  <Field label="request_id" value={row.request_id} />
                  <Field label="agent_id" value={row.agent_id} />
                  <Field label="approval_id" value={row.approval_id ?? "null"} />
                  <Field label="created_at" value={row.created_at} note="written by gateway at decision time" />
                  <Field
                    label="resolved_at"
                    value={row.resolved_at ?? "null"}
                    note={row.resolved_at ? "written by executor at execution time" : undefined}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
