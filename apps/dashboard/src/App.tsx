import { useCallback, useEffect, useState } from "react";
import { LogOut, ShieldCheck } from "lucide-react";
import { SessionTranscript } from "./components/SessionTranscript";
import { RiskGauge } from "./components/RiskGauge";
import { FactorBars } from "./components/FactorBars";
import { ApprovalCard } from "./components/ApprovalCard";
import { IncidentTimeline } from "./components/IncidentTimeline";
import { ActionSimulator } from "./components/ActionSimulator";
import { AttackLab } from "./components/AttackLab";
import { LoginPage, clearAuthenticated, isAuthenticated } from "./components/LoginPage";
import { getPolicy } from "./api/gateway";
import { useActivityStream } from "./hooks/useActivityStream";
import type { PolicySnapshot } from "./types/api";
import type { CurrentDecision } from "./lib/currentDecision";

// One screen, three fixed columns, no router: Agent Session | Decision |
// Approval Queue + Incident Timeline. A cosmetic client-side login gate
// sits in front of it for demo purposes — see components/LoginPage.tsx;
// it is not part of the security model (auth/RBAC is explicitly out of
// scope for the engine per CLAUDE.md).
function App() {
  const [authed, setAuthed] = useState(() => isAuthenticated());
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

  if (!authed) {
    return <LoginPage onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div className="grid h-screen grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)] grid-rows-[auto_1fr] bg-ground text-ink">
      <header className="col-span-3 flex items-center gap-2.5 border-b border-border bg-surface/60 px-5 py-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-soft text-brand">
          <ShieldCheck size={18} strokeWidth={2.25} />
        </span>
        <div className="leading-tight">
          <h1 className="text-[15px] font-semibold text-ink">Sentinel AI</h1>
          <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-ink-muted">
            Runtime Security Gateway
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            clearAuthenticated();
            setAuthed(false);
          }}
          className="sentinel-btn sentinel-btn-ghost ml-auto flex items-center gap-1.5 px-3 py-1.5 text-xs"
        >
          <LogOut size={13} />
          Sign out
        </button>
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
