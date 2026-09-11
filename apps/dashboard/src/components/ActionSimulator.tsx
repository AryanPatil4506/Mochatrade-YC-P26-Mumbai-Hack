import { useState } from "react";
import { FlaskConical } from "lucide-react";
import { evaluateAction } from "../api/gateway";
import { execute } from "../api/executor";
import { ACTION_FIXTURES, freshAction } from "../data/fixtures";
import type { CurrentDecision } from "../lib/currentDecision";

interface Props {
  onResult: (decision: CurrentDecision, executed?: boolean) => void;
}

// Drives POST /v1/gateway/evaluate directly with a known ProposedAction and,
// on ALLOW, immediately redeems the returned capability_token against
// POST /v1/execute — the one flow that exercises the real end-to-end
// enforcement chain (evaluate -> token -> executor verification -> tool
// run) on demand, since the chat-driven agent flow never calls the real
// executor (services/agent/graph/nodes.py's handle_decision is a stub).
export function ActionSimulator({ onResult }: Props) {
  const [running, setRunning] = useState<string | null>(null);
  const [lastNote, setLastNote] = useState<string | null>(null);

  async function run(fixtureId: string) {
    const fixture = ACTION_FIXTURES.find((f) => f.id === fixtureId);
    if (!fixture) return;
    setRunning(fixtureId);
    setLastNote(null);
    try {
      const action = freshAction(fixture);
      const decision = await evaluateAction(action);
      onResult(
        {
          source: "simulator",
          request_id: decision.request_id,
          decision: decision.decision,
          risk_score: decision.risk_score,
          risk_factors: decision.risk_factors,
          policy_rule_triggered: decision.policy_rule_triggered,
        },
        false,
      );

      if (decision.capability_token) {
        const result = await execute(action, decision.capability_token);
        setLastNote(`${fixture.label}: ${decision.decision}, executed=${result.executed}, success=${result.success}`);
        onResult(
          {
            source: "simulator",
            request_id: decision.request_id,
            decision: decision.decision,
            risk_score: decision.risk_score,
            risk_factors: decision.risk_factors,
            policy_rule_triggered: decision.policy_rule_triggered,
          },
          result.executed,
        );
      } else {
        setLastNote(`${fixture.label}: ${decision.decision} (no capability token — not executed)`);
      }
    } catch (e) {
      setLastNote(e instanceof Error ? e.message : "simulator run failed");
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="border-b border-border p-4">
      <p className="mb-2.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-muted">
        <FlaskConical size={13} className="text-brand" />
        Action Simulator
      </p>
      <div className="flex flex-wrap gap-1.5">
        {ACTION_FIXTURES.map((f) => (
          <button
            key={f.id}
            disabled={running !== null}
            onClick={() => run(f.id)}
            className="sentinel-btn sentinel-btn-ghost px-2.5 py-1.5 text-xs disabled:opacity-50"
          >
            {running === f.id ? "running…" : f.label}
          </button>
        ))}
      </div>
      {lastNote && <p className="mt-2.5 font-mono text-[11px] text-ink-muted">{lastNote}</p>}
    </div>
  );
}
