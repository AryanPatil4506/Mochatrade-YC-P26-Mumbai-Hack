import { useEffect, useRef, useState } from "react";
import { sessionEventsUrl } from "../api/agent";
import type { AgentSessionEvent } from "../types/api";

export interface TranscriptLine {
  id: number;
  event: AgentSessionEvent;
}

interface SessionEventsState {
  lines: TranscriptLine[];
  connected: boolean;
  lastDecision: { request_id: string; decision: string; risk_score: number } | null;
  turnInFlight: boolean;
}

// Subscribes to the agent's per-session SSE stream
// (GET /v1/agent/sessions/{id}/events, services/agent/events.py) — genuinely
// fed turn-by-turn by services/agent/graph/nodes.py, distinct from the
// executor's shared activity bus used by useActivityStream().
export function useSessionEvents(sessionId: string | null): SessionEventsState {
  const [lines, setLines] = useState<TranscriptLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastDecision, setLastDecision] = useState<SessionEventsState["lastDecision"]>(null);
  const [turnInFlight, setTurnInFlight] = useState(false);
  const counter = useRef(0);

  useEffect(() => {
    setLines([]);
    setLastDecision(null);
    setTurnInFlight(false);
    if (!sessionId) {
      setConnected(false);
      return;
    }

    const source = new EventSource(sessionEventsUrl(sessionId));

    const handle = (raw: MessageEvent<string>) => {
      let event: AgentSessionEvent;
      try {
        event = JSON.parse(raw.data) as AgentSessionEvent;
      } catch {
        return;
      }
      counter.current += 1;
      setLines((prev) => [...prev, { id: counter.current, event }]);

      if (event.type === "user_message") setTurnInFlight(true);
      if (event.type === "decision") {
        setLastDecision({ request_id: event.request_id, decision: event.decision, risk_score: event.risk_score });
      }
      if (event.type === "turn_complete") setTurnInFlight(false);
    };

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    // sse-starlette sends named events (event: <type>); EventSource's
    // generic "message" handler only fires for unnamed events, so listen
    // for every event.type this stream can emit.
    const eventTypes: AgentSessionEvent["type"][] = [
      "user_message",
      "taint_read",
      "plan",
      "proposed_action",
      "decision",
      "tool_result",
      "assistant_message",
      "turn_complete",
      "session_closed",
    ];
    for (const t of eventTypes) source.addEventListener(t, handle as EventListener);

    return () => {
      source.close();
      setConnected(false);
    };
  }, [sessionId]);

  return { lines, connected, lastDecision, turnInFlight };
}
