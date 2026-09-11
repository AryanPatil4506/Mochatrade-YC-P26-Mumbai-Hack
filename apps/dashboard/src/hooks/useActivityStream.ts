import { useEffect, useRef, useState } from "react";
import { activityStreamUrl } from "../api/executor";
import type { ActivityEvent } from "../types/api";

type DecisionActivityEvent = Extract<ActivityEvent, { type: "decision" }>;

interface ActivityStreamState {
  events: ActivityEvent[];
  connected: boolean;
  latestDecision: DecisionActivityEvent | null;
}

const MAX_BUFFER = 200;

// Subscribes to the executor's shared activity bus (GET /v1/events,
// services/executor/events.py) — carries "decision" events relayed from the
// gateway and "execution"/"execution_denied" events from the executor
// itself. This is the single, service-wide event stream — distinct from
// the per-session agent stream in useSessionEvents.
export function useActivityStream(onDecision?: (e: DecisionActivityEvent) => void) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const onDecisionRef = useRef(onDecision);
  onDecisionRef.current = onDecision;

  useEffect(() => {
    const source = new EventSource(activityStreamUrl);

    const handle = (raw: MessageEvent<string>) => {
      let event: ActivityEvent;
      try {
        event = JSON.parse(raw.data) as ActivityEvent;
      } catch {
        return;
      }
      setEvents((prev) => [event, ...prev].slice(0, MAX_BUFFER));
      if (event.type === "decision") onDecisionRef.current?.(event);
    };

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    const eventTypes: ActivityEvent["type"][] = ["decision", "execution", "execution_denied"];
    for (const t of eventTypes) source.addEventListener(t, handle as EventListener);

    return () => {
      source.close();
      setConnected(false);
    };
  }, []);

  const latestDecision = (events.find((e) => e.type === "decision") as DecisionActivityEvent | undefined) ?? null;

  return { events, connected, latestDecision } satisfies ActivityStreamState;
}
