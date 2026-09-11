import { useCallback, useEffect, useState } from "react";
import { SessionTranscript } from "./components/SessionTranscript";
import { RiskGauge } from "./components/RiskGauge";
import { FactorBars } from "./components/FactorBars";
import { ApprovalCard } from "./components/ApprovalCard";
import { IncidentTimeline } from "./components/IncidentTimeline";
import { ActionSimulator } from "./components/ActionSimulator";
import { AttackLab } from "./components/AttackLab";
import { getPolicy } from "./api/gateway";
import { useActivityStream } from "./hooks/useActivityStream";
import type { PolicySnapshot } from "./types/api";
import type { CurrentDecision } from "./lib/currentDecision";

// One screen, three fixed columns, no router, no login — per CLAUDE.md's
// dashboard spec: Agent Session | Decision | Approval Queue + Incident
// Timeline.
function App() {
  const [policy, setPolicy] = useState<PolicySnapshot | null>(null);
  const [current, setCurrent] = useState<CurrentDecision | null>(null);
  const [approvalRefreshSignal, setApprovalRefreshSignal] = useState(0);

  useEffect(() => {
    getPolicy().then(setPolicy).catch(() => setPolicy(null));
  }, []);

  const { events: activityEvents } = useActivityStream((decisionEvent) => {
    if (decisionEvent.decision === "REQUIRE_APPROVAL") {
      setApprovalRefreshSignal((n) => n + 1);
    }
  });

  const onSessionDecision = useCallback((d: { request_id: string; decision: string; risk_score: number }) => {
    setCurrent({
      source: "session",
      request_id: d.request_id,
      decision: d.decision as CurrentDecision["decision"],
      risk_score: d.risk_score,
      risk_factors: null,
    });
    if (d.decision === "REQUIRE_APPROVAL") setApprovalRefreshSignal((n) => n + 1);
  }, []);

  const onSimulatorResult = useCallback((decision: CurrentDecision) => {
    setCurrent(decision);
    if (decision.decision === "REQUIRE_APPROVAL") setApprovalRefreshSignal((n) => n + 1);
  }, []);

  return (
    <div className="grid h-screen grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)] grid-rows-[auto_1fr] bg-ground text-ink">
      <header className="col-span-3 flex items-center border-b border-border px-4 py-2">
        <h1 className="text-sm font-semibold tracking-wide text-ink-muted">
          SENTINEL AI <span className="text-ink">— Runtime Security Gateway</span>
        </h1>
      </header>

      <section className="col-start-1 row-start-2 flex flex-col overflow-hidden border-r border-border">
        <SessionTranscript onDecision={onSessionDecision} />
      </section>

      <section className="col-start-2 row-start-2 flex flex-col overflow-hidden border-r border-border">
        <ActionSimulator onResult={onSimulatorResult} />
        <AttackLab onResult={onSimulatorResult} />
        <div className="flex-1 overflow-y-auto">
          <RiskGauge decision={current} />
          <FactorBars decision={current} policy={policy} />
        </div>
      </section>

      <section className="col-start-3 row-start-2 flex flex-col overflow-hidden">
        <ApprovalCard refreshSignal={approvalRefreshSignal} />
        <IncidentTimeline liveEvents={activityEvents} />
      </section>
    </div>
  );
}

export default App;
