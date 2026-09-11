# Sentinel AI — Build Specification
### Team Paragons | Runtime Security Gateway for Autonomous AI Agents

This document defines the shared contracts and per-person scope needed to build all four parts **in parallel** without blocking on each other. Read Section 2 together as a team before splitting off — everything else depends on agreeing to these shapes first.

---

## 1. System Overview

```
Agent (Zone B) → proposes action
      ↓
Sentinel Gateway (Zone C) → intercepts, scores, decides
      ↓
ALLOW → Sandbox Tools (Zone E)
REQUIRE_APPROVAL → Human Queue (Zone D) → Approve/Reject → Zone E
BLOCK → no execution
      ↓ (always)
Audit Logger (Zone F) → SQLite + Incident Timeline
```

Core rule: **the LLM explains and interprets — it never authorizes itself.** Every decision is deterministic and logged.

---

## 2. Shared Data Contracts

These are the interfaces between parts. Lock the field names and types now — changing them mid-hackathon breaks everyone downstream.

### 2.1 Proposed Action Object
Produced by **Part 1**, consumed by **Part 2** and **Part 3**.

```json
{
  "request_id": "uuid",
  "agent_id": "string",
  "session_id": "uuid",
  "timestamp": "ISO8601",
  "tool_name": "email | database | crm | ticketing | web",
  "operation": "read | write | update | delete | send",
  "arguments": { "...": "tool-specific parameters" },
  "target_resource": "string",
  "destination": "string | null",
  "context": {
    "user_request": "string — original natural-language instruction",
    "untrusted_content_sources": [
      {
        "source": "email | ticket | web_page | database_record",
        "content": "string — raw text the agent read before proposing this action"
      }
    ]
  }
}
```

**Required fields:** `request_id`, `agent_id`, `session_id`, `timestamp`, `tool_name`, `operation`, `target_resource`.
**Critical for Part 2:** `context.untrusted_content_sources` must be populated whenever the agent's action was influenced by external content (email body, ticket text, scraped page). If Part 1 skips this, prompt-injection detection has nothing to scan.

### 2.2 Decision Object
Produced by **Part 3** (the deterministic decision layer), consumed by **Part 1** (dashboard), **Part 4** (sandbox executor + audit).

```json
{
  "request_id": "uuid",
  "decision": "ALLOW | REQUIRE_APPROVAL | BLOCK",
  "risk_score": 0,
  "risk_factors": {
    "tool_sensitivity": 0,
    "data_sensitivity": 0,
    "privilege_level": 0,
    "destination_risk": 0,
    "reversibility": 0,
    "injection_signal": 0,
    "behavioral_anomaly": 0
  },
  "policy_rule_triggered": "string | null",
  "explanation": "string — LLM-generated human-readable reason",
  "requires_human_approval": true,
  "approval_id": "uuid | null",
  "timestamp": "ISO8601",
  "audit_log_id": "uuid"
}
```

**Required fields:** `request_id`, `decision`, `risk_score`, `risk_factors`, `timestamp`, `audit_log_id`.
Every `risk_factors` sub-score is 0–100; `risk_score` is the weighted composite Part 2 computes and Part 3 consumes as input to its policy rules.

### 2.3 Approval Record
Produced by **Part 3** (human queue), consumed by **Part 4** (executor waits on this).

```json
{
  "approval_id": "uuid",
  "request_id": "uuid",
  "status": "PENDING | APPROVED | REJECTED",
  "approver_id": "string | null",
  "reason": "string | null",
  "resolved_at": "ISO8601 | null"
}
```

### 2.4 Audit Log Entry
Produced by **Part 4**, written once per request lifecycle — this is the single source of truth for the Incident Timeline.

```json
{
  "audit_log_id": "uuid",
  "request_id": "uuid",
  "agent_id": "string",
  "tool_name": "string",
  "operation": "string",
  "risk_score": 0,
  "decision": "ALLOW | REQUIRE_APPROVAL | BLOCK",
  "approval_id": "uuid | null",
  "executed": true,
  "created_at": "ISO8601",
  "resolved_at": "ISO8601 | null"
}
```

### 2.5 Risk Threshold Bands (draft — finalize as a team)
Starting point based on the diagrammed design; adjust once Part 2's scoring is calibrated against real test cases:

| Risk Score | Decision |
|---|---|
| 0–30 | ALLOW |
| 30–60 | ALLOW + LOG |
| 60–80 | REQUIRE_APPROVAL |
| 80–100 | BLOCK |

---

## 3. Section Breakdown

### Part 1 — Agent & Client Layer
**Covers:** Zone A (User/Presentation) + Zone B (AI Agent)

- React + Tailwind dashboard: shows agent actions, risk scores, incidents, approval queue
- FastAPI backend: session handling, event coordination, enforcement hooks
- LangGraph agent orchestrator: proposes actions only — never calls tools directly
- Structured Tool Request builder: assembles the **Proposed Action Object** (2.1)
- OpenAI API integration for agent reasoning

**Outputs:** Proposed Action Object → Gateway
**Depends on:** Nothing to start (can build against a mocked gateway response)
**Definition of done:** Agent can generate a realistic tool-call proposal end-to-end and render an incoming Decision Object on the dashboard.

### Part 2 — Detection & Risk Engine
**Covers:** Detection & Analysis stage inside Zone C

- Prompt-injection detection: rule-based scanner + DeBERTa classifier over `untrusted_content_sources`
- Data classification: Presidio (PII) + custom rules (API keys, credentials, financial data)
- Contextual risk scoring: weighted combination of tool sensitivity, data sensitivity, privilege, destination, reversibility, injection signal, behavioral anomaly
- Behavioral anomaly detection: Isolation Forest over embedding similarity (sentence-transformers)

**Inputs:** Proposed Action Object (2.1)
**Outputs:** populated `risk_factors` + composite `risk_score` (feeds into 2.2)
**Depends on:** Agreed field names in 2.1; can build/test against sample JSON before Part 1 is live
**Definition of done:** Given any Proposed Action Object (real or mocked), returns a scored, weighted risk breakdown with example weights (e.g., 20% tool sensitivity, 20% data sensitivity, 15% privilege, 10% destination, 15% reversibility, 15% injection, 5% anomaly).

### Part 3 — Policy Engine, Decision Logic & Human Approval
**Covers:** Policy Engine + Deterministic Decision (Zone C) + Zone D (Human Approval)

- Agent identity & least-privilege enforcement (role, permissions, allowed tools/operations)
- Policy engine: static allow/block/log rules layered on top of risk score
- Deterministic decision layer: applies threshold bands (2.5) to produce the final **Decision Object** (2.2) — no LLM in this path
- Human approval queue UI: pauses action, shows risk factors + reason, approver approves/reject → **Approval Record** (2.3)

**Inputs:** Risk-scored Proposed Action Object from Part 2
**Outputs:** Decision Object (2.2), Approval Record (2.3)
**Depends on:** Part 2's risk_factors shape
**Definition of done:** Any risk-scored request deterministically resolves to ALLOW / REQUIRE_APPROVAL / BLOCK, with REQUIRE_APPROVAL correctly pausing execution until a human resolves it.

### Part 4 — Sandbox Tools & Audit/Data Layer
**Covers:** Zone E (Sandbox Tools) + Zone F (Data/Audit) + Attack Simulation Lab

- Mocked enterprise tools: CRM, ticketing, email, SQL/DB — authorized calls only, no direct agent access
- Attack Simulation Lab: generates prompt-injection payloads, privilege-abuse attempts, destructive SQL, exfiltration attempts for testing
- Audit logger: writes **Audit Log Entry** (2.4) for every request
- SQLite schema: rules, policies, events, scores, incidents, records
- Incident Timeline: renders blocked/suspicious/allowed history for the dashboard

**Inputs:** Decision Object (2.2) — only executes on ALLOW or resolved APPROVED
**Outputs:** Audit Log Entry (2.4) → dashboard (Part 1)
**Depends on:** Part 3's Decision Object shape
**Definition of done:** Executor only fires tool calls when decision permits it; every request — regardless of outcome — produces one audit record visible in the timeline.

---

## 4. Integration Checklist (do this before splitting off)

- [ ] All 4 people agree on field names/types in Sections 2.1–2.4 — treat this as frozen once building starts
- [ ] Agree on risk weight percentages for Part 2's composite score
- [ ] Agree on the threshold bands in 2.5 (or explicitly mark as "tune later")
- [ ] Decide on a shared repo structure / branch-per-part convention
- [ ] Part 1 and Part 2 agree on 2–3 sample Proposed Action Objects (including at least one with injected malicious content) to use as shared test fixtures
- [ ] Part 3 and Part 4 agree on what "executed: true/false" means for a BLOCK'd request in the audit log

## 5. Demo Flow

Walk judges through the pipeline left to right, each person narrating their zone:
1. **Part 1:** agent receives a request, proposes a tool call
2. **Part 2:** show a benign vs. an injected request side by side, compare risk scores
3. **Part 3:** show the same two requests resolve to ALLOW vs. REQUIRE_APPROVAL/BLOCK, approve one live
4. **Part 4:** show the incident timeline logging both outcomes, then run one Attack Simulation Lab scenario live
