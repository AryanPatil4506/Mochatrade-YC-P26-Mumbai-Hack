import { useEffect, useState } from "react";
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
    <div className="border-b border-border p-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Attack Simulation Lab</p>
      <div className="flex flex-wrap gap-1.5">
        {scenarios.map((s) => (
          <button
            key={s.id}
            disabled={running !== null}
            title={s.description}
            onClick={() => run(s.id)}
            className="rounded border border-border bg-surface px-2 py-1 text-xs text-ink hover:bg-surface-raised disabled:opacity-50"
          >
            {running === s.id ? "running…" : s.name}
          </button>
        ))}
        <button
          disabled={running !== null}
          onClick={runCompromise}
          title="POST /v1/agent/simulate-compromise — calls the executor directly with a forged token, bypassing the gateway"
          className="rounded border border-block/50 bg-block/10 px-2 py-1 text-xs text-block hover:bg-block/20 disabled:opacity-50"
        >
          {running === "simulate-compromise" ? "running…" : "Simulate compromised agent"}
        </button>
      </div>
      {note && <p className="mt-2 font-mono text-[11px] text-ink-muted">{note}</p>}
    </div>
  );
}
