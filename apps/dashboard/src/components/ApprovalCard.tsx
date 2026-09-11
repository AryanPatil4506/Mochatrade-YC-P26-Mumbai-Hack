import { useCallback, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { listApprovals, resolveApproval } from "../api/approvals";
import type { ApprovalRecord } from "../types/contracts";

interface Props {
  // Bumped whenever the activity stream sees a REQUIRE_APPROVAL decision, so
  // the list refreshes immediately instead of waiting for the safety-net
  // poll below.
  refreshSignal: number;
}

const SAFETY_NET_POLL_MS = 5000;

export function ApprovalCard({ refreshSignal }: Props) {
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [selected, setSelected] = useState(0);
  const [tokens, setTokens] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listApprovals("PENDING");
      setApprovals(list);
      setSelected((prev) => Math.min(prev, Math.max(0, list.length - 1)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to list approvals");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, refreshSignal]);

  // Safety-net poll — GET /v1/approvals?status=PENDING isn't itself pushed
  // over SSE; the "decision" event on the shared bus is the primary trigger
  // above, this just covers gaps (e.g. an approval created before this tab
  // connected).
  useEffect(() => {
    const id = setInterval(refresh, SAFETY_NET_POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const resolve = useCallback(
    async (approval_id: string, status: "APPROVED" | "REJECTED") => {
      setBusy(approval_id);
      setError(null);
      try {
        const res = await resolveApproval(approval_id, { status, approver_id: "dashboard-operator" });
        if (res.capability_token) {
          setTokens((prev) => ({ ...prev, [approval_id]: res.capability_token! }));
        }
        await refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : "failed to resolve approval");
      } finally {
        setBusy(null);
      }
    },
    [refresh],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const current = approvals[selected];
      if (!current || busy) return;
      if (e.key === "a") resolve(current.approval_id, "APPROVED");
      if (e.key === "r") resolve(current.approval_id, "REJECTED");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [approvals, selected, busy, resolve]);

  return (
    <div className="border-b border-border p-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
          <CheckCircle2 size={13} className="text-brand" />
          Approval Queue {approvals.length > 0 && `(${approvals.length})`}
        </h2>
        <span className="font-mono text-[10px] text-ink-muted">a = approve · r = reject</span>
      </div>

      {error && <p className="pt-2 text-xs text-block">{error}</p>}

      <div className="mt-3 max-h-64 space-y-2 overflow-y-auto">
        {approvals.length === 0 && <p className="text-sm text-ink-muted">No pending approvals.</p>}
        {approvals.map((a, i) => (
          <div
            key={a.approval_id}
            onClick={() => setSelected(i)}
            className={`sentinel-card cursor-pointer p-3 text-sm transition-colors ${
              i === selected ? "border-brand/50" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-ink-muted">req {a.request_id.slice(0, 8)}</span>
              <span className="font-mono text-xs text-ink-muted">appr {a.approval_id.slice(0, 8)}</span>
            </div>
            <div className="mt-2.5 flex gap-2">
              <button
                disabled={busy === a.approval_id}
                onClick={(e) => {
                  e.stopPropagation();
                  resolve(a.approval_id, "APPROVED");
                }}
                className="sentinel-btn flex-1 bg-allow px-2 py-1.5 text-xs text-[#06210f] hover:brightness-110 disabled:opacity-50"
              >
                Approve
              </button>
              <button
                disabled={busy === a.approval_id}
                onClick={(e) => {
                  e.stopPropagation();
                  resolve(a.approval_id, "REJECTED");
                }}
                className="sentinel-btn flex-1 bg-surface-raised px-2 py-1.5 text-xs text-block ring-1 ring-inset ring-block/40 hover:bg-block/10 disabled:opacity-50"
              >
                Reject
              </button>
            </div>
            {tokens[a.approval_id] && (
              <p className="mt-2 truncate font-mono text-[10px] text-ink-muted" title={tokens[a.approval_id]}>
                token: {tokens[a.approval_id].slice(0, 24)}… (not auto-redeemed — no endpoint exposes this
                action's original arguments to replay against /v1/execute)
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
