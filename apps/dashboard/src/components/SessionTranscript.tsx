import { useEffect, useRef, useState } from "react";
import { MessageSquare } from "lucide-react";
import { createSession, sendMessage } from "../api/agent";
import { useSessionEvents } from "../hooks/useSessionEvents";

// The four agent IDs from config/agent_registry.yaml — no endpoint exposes
// this list today (it's server-side-only config consumed by
// services/gateway/detection/privilege.py), so it's hardcoded here.
const AGENT_IDS = ["crm-assistant-01", "support-triage-01", "reporting-bot-01", "outreach-bot-01"];

interface Props {
  onDecision: (d: { request_id: string; decision: string; risk_score: number }) => void;
}

export function SessionTranscript({ onDecision }: Props) {
  const [agentId, setAgentId] = useState(AGENT_IDS[0]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { lines, connected, lastDecision, turnInFlight } = useSessionEvents(sessionId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (lastDecision) onDecision(lastDecision);
  }, [lastDecision, onDecision]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [lines]);

  async function handleNewSession() {
    setCreating(true);
    setError(null);
    try {
      const res = await createSession(agentId);
      setSessionId(res.session_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to create session");
    } finally {
      setCreating(false);
    }
  }

  async function handleSend() {
    if (!sessionId || !draft.trim()) return;
    setError(null);
    try {
      await sendMessage(sessionId, draft.trim());
      setDraft("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to send message");
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border p-4">
        <h2 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
          <MessageSquare size={13} className="text-brand" />
          Agent Session
        </h2>
        <div className="mt-3 flex gap-2">
          <select
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-surface-raised px-2.5 py-1.5 text-sm text-ink outline-none focus:border-brand/60"
          >
            {AGENT_IDS.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <button
            onClick={handleNewSession}
            disabled={creating}
            className="sentinel-btn sentinel-btn-primary px-3 py-1.5 text-sm disabled:opacity-50"
          >
            New session
          </button>
        </div>
        {sessionId && (
          <p className="mt-2.5 flex items-center gap-1.5 truncate font-mono text-[11px] text-ink-muted">
            <span
              className="h-1.5 w-1.5 flex-none rounded-full"
              style={{ background: connected ? "var(--color-allow)" : "var(--color-block)" }}
            />
            {sessionId}
          </p>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-2 overflow-y-auto p-4">
        {!sessionId && <p className="text-sm text-ink-muted">Create a session to start.</p>}
        {lines.map(({ id, event }) => (
          <TranscriptLine key={id} event={event} />
        ))}
        {turnInFlight && <p className="animate-pulse text-xs text-ink-muted">thinking…</p>}
      </div>

      {error && <p className="border-t border-border px-4 py-2 text-xs text-block">{error}</p>}

      <div className="flex gap-2 border-t border-border p-4">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={!sessionId}
          placeholder={sessionId ? "Ask the agent to do something…" : "Create a session first"}
          className="flex-1 rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm text-ink placeholder:text-ink-muted/70 outline-none focus:border-brand/60 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!sessionId || !draft.trim()}
          className="sentinel-btn sentinel-btn-primary px-4 py-2 text-sm disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function TranscriptLine({ event }: { event: import("../types/api").AgentSessionEvent }) {
  switch (event.type) {
    case "user_message":
      return <div className="rounded-lg bg-surface-raised px-3 py-2 text-sm text-ink">{event.content}</div>;
    case "assistant_message":
      return <div className="rounded-lg border border-border px-3 py-2 text-sm text-ink">{event.content}</div>;
    case "taint_read":
      // Tainted content visually distinct — this line came from an
      // untrusted external source (email/ticket/web_page/database_record).
      return (
        <div className="rounded-lg border border-dashed border-flagged/50 bg-flagged/10 px-3 py-2 text-xs text-flagged">
          ⚠ read untrusted <span className="font-mono">{event.source}</span>:{event.reference}
        </div>
      );
    case "plan":
      return (
        <div className="px-3 text-xs text-ink-muted">
          planning <span className="font-mono">{event.function_name}</span>
        </div>
      );
    case "proposed_action":
      return (
        <div className="px-3 text-xs text-ink-muted">
          proposed <span className="font-mono">{event.tool_name}.{event.operation}</span> ·{" "}
          <span className="font-mono">{event.request_id.slice(0, 8)}</span>
        </div>
      );
    case "decision":
      return (
        <div className="px-3 text-xs font-medium text-ink-muted">
          gateway decision: <span className="font-mono">{event.decision}</span> (score {event.risk_score})
        </div>
      );
    case "tool_result":
      return <div className="px-3 text-xs italic text-ink-muted">{event.result ?? "(no result)"}</div>;
    case "turn_complete":
    case "session_closed":
      return null;
    default:
      return null;
  }
}
