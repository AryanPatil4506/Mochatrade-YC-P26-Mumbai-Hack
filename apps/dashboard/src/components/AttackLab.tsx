import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { listLabScenarios, runLabScenario } from "../api/executor";
import { simulateCompromise } from "../api/agent";
import type { LabScenarioMeta } from "../types/api";
import type { CurrentDecision } from "../lib/currentDecision";

interface Props {
  onResult: (decision: CurrentDecision) => void;
}

export function AttackLab({ onResult }: Props) {
  const [scenarios, setScenarios] = useState<LabScenarioMeta[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    listLabScenarios().then(setScenarios).catch(() => setScenarios([]));
  }, []);

  async function run(id: string) {
    setRunning(id);
    setNote(null);
    try {
      const result = await runLabScenario(id);
      onResult({
        source: "lab",
        request_id: result.decision.request_id,
        decision: result.decision.decision,
        risk_score: result.decision.risk_score,
        risk_factors: result.decision.risk_factors,
        policy_rule_triggered: result.decision.policy_rule_triggered,
      });
      setNote(`${id}: ${result.decision.decision} · executed=${result.executed}`);
    } catch (e) {
      setNote(e instanceof Error ? e.message : "lab run failed");
    } finally {
      setRunning(null);
    }
  }

  async function runCompromise() {
    setRunning("simulate-compromise");
    setNote(null);
    try {
      const res = await simulateCompromise();
      const reason = res.executor_response?.detail?.reason;
      setNote(`compromised-agent test: ${res.outcome} (status ${res.status_code}${reason ? `, reason=${reason}` : ""})`);
    } catch (e) {
      setNote(e instanceof Error ? e.message : "compromise test failed");
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="border-b border-border p-4">
      <p className="mb-2.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
        <ShieldAlert size={13} className="text-brand" />
        Attack Simulation Lab
      </p>
      <div className="flex flex-wrap gap-1.5">
        {scenarios.map((s) => (
          <button
            key={s.id}
            disabled={running !== null}
            title={s.description}
            onClick={() => run(s.id)}
            className="sentinel-btn sentinel-btn-ghost px-2.5 py-1.5 text-xs disabled:opacity-50"
          >
            {running === s.id ? "running…" : s.name}
          </button>
        ))}
        <button
          disabled={running !== null}
          onClick={runCompromise}
          title="POST /v1/agent/simulate-compromise — calls the executor directly with a forged token, bypassing the gateway"
          className="sentinel-btn bg-block/15 px-2.5 py-1.5 text-xs text-block ring-1 ring-inset ring-block/40 hover:bg-block/25 disabled:opacity-50"
        >
          {running === "simulate-compromise" ? "running…" : "Simulate compromised agent"}
        </button>
      </div>
      {note && <p className="mt-2.5 font-mono text-[11px] text-ink-muted">{note}</p>}
    </div>
  );
}
