# Part 4 Integration Contract

This document explains only how Part 4 integrates with Parts 1, 2, and 3, based on the actual implementation in the repository and the existing contracts in `part4.md`.

This is intentionally limited to integration behavior. It does not define new interfaces or modify application code.

---

## 1. Scope and source of truth

The actual Part 4 runtime contract is implemented in:

- `executor/model.py` — dataclasses for `ProposedAction`, `DecisionObject`, and `ExecutionResult`
- `executor/executor.py` — execution enforcement logic
- `audit/service.py` — audit and approval persistence facade
- `audit/repository.py` — SQLite persistence
- `api/routes.py` and `api/attack_routes.py` — currently exposed API surface
- `database/schema.sql` — audit schema

The key enforcement rule in the code is:

```python
if proposed_action.request_id != decision.request_id:
    return ExecutionResult(... error="Execution blocked: request id mismatch between proposed action and decision")
```

This is the core linkage between the upstream objects.

---

## 2. What Part 4 receives from Part 3

Part 4 receives a `DecisionObject` from Part 3.

Exact dataclass definition from `executor/model.py`:

```python
@dataclass
class DecisionObject:
    request_id: str
    decision: str
    risk_score: float = 0
    risk_factors: Dict[str, Any] = field(default_factory=dict)
    policy_rule_triggered: Optional[str] = None
    explanation: str = ""
    requires_human_approval: bool = False
    approval_id: Optional[str] = None
    timestamp: str = ""
    audit_log_id: Optional[str] = None
    approval_status: Optional[str] = None
```

The required decision fields used by Part 4 are:

- `request_id`
- `decision`
- `risk_score`
- `risk_factors`
- `timestamp`
- `audit_log_id`

Part 4 also reads these when relevant:

- `requires_human_approval`
- `approval_id`
- `approval_status`
- `explanation`
- `policy_rule_triggered`

Important implementation note: the actual code adds `approval_status` as a runtime field, even though the original Part 4 spec lists `approval_id` and `requires_human_approval` as the main approval metadata. The executor uses `decision.approval_status` to decide whether a `REQUIRE_APPROVAL` request is approved, rejected, or still pending.

---

## 3. Exact Decision Object fields required

The Part 4 design contract in `part4.md` states the Decision Object must look like this:

```json
{
  "request_id": "uuid",
  "decision": "ALLOW | REQUIRE_APPROVAL | BLOCK",
  "risk_score": 0,
  "risk_factors": {},
  "policy_rule_triggered": "string | null",
  "explanation": "string",
  "requires_human_approval": true,
  "approval_id": "uuid | null",
  "timestamp": "ISO8601",
  "audit_log_id": "uuid"
}
```

The code does not enforce every field at runtime, but the execution logic clearly relies on these values:

- `request_id` — must match the Proposed Action
- `decision` — must be one of `ALLOW`, `REQUIRE_APPROVAL`, or `BLOCK`
- `approval_status` — used by `execute_request()` for the approval path
- `approval_id` — carried into audit logs
- `audit_log_id` — used by `AuditService.create_log()`; if missing, it is generated

The Part 4 spec requires `request_id`, `decision`, `risk_score`, `risk_factors`, `timestamp`, and `audit_log_id` to be present. The code aligns with that pattern, while also adding optional runtime approval state.

---

## 4. What Part 4 additionally needs from the Proposed Action Object

Part 4 does not have enough information to execute a tool from the Decision Object alone. It also needs the original `ProposedAction`.

Exact dataclass definition from `executor/model.py`:

```python
@dataclass
class ProposedAction:
    request_id: str
    agent_id: str
    session_id: str
    timestamp: str
    tool_name: str
    operation: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    target_resource: Optional[str] = None
    destination: Optional[str] = None
    context: Optional[Dict[str, Any]] = field(default_factory=dict)
```

For execution, Part 4 primarily needs these fields:

- `request_id`
- `agent_id`
- `tool_name`
- `operation`
- `arguments`
- `target_resource`
- `destination`

That matches the Part 4 spec. The other fields are preserved for traceability, audit context, and debugging.

The actual execution call is:

```python
execute_request(
    proposed_action: ProposedAction,
    decision: DecisionObject
) -> ExecutionResult
```

This is the interface the code expects.

---

## 5. How `request_id` connects the objects

`request_id` is the shared correlation key across the workflow.

The code enforces this in `executor/executor.py`:

```python
if proposed_action.request_id != decision.request_id:
    return ExecutionResult(... error="Execution blocked: request id mismatch between proposed action and decision")
```

The same `request_id` is also used in audit persistence:

```python
log = AuditLog(
    audit_log_id=audit_log_id,
    request_id=proposed_action.request_id,
    agent_id=proposed_action.agent_id,
    tool_name=proposed_action.tool_name,
    operation=proposed_action.operation,
    risk_score=int(decision.risk_score),
    decision=decision.decision,
    approval_id=decision.approval_id,
    executed=executed,
    created_at=_now_iso(),
    resolved_at=resolved_at,
)
```

And in approval records:

```python
ApprovalRecord(
    approval_id=approval_id,
    request_id=request_id,
    status=status,
    ...
)
```

Therefore:

- Part 1/Part 2 generate the Proposed Action with a `request_id`
- Part 3 produces a Decision Object with the same `request_id`
- Part 4 rejects any mismatch before execution
- The audit log and approval records are keyed by the same `request_id`

---

## 6. ALLOW -> execution flow

The actual execution rule in `executor/executor.py` is:

```python
if decision.decision == "BLOCK":
    ... block

if decision.decision == "REQUIRE_APPROVAL":
    if decision_state == "APPROVED":
        pass
    else:
        return ExecutionResult(... error="Execution blocked: approval is not approved")

result = execute_tool(
    tool_name=proposed_action.tool_name,
    operation=proposed_action.operation,
    arguments=proposed_action.arguments,
    target_resource=proposed_action.target_resource,
    destination=proposed_action.destination,
)
```

This means:

1. `request_id` must match.
2. `decision.decision` must not be `BLOCK`.
3. If `decision.decision` is `REQUIRE_APPROVAL`, the code requires `approval_status == "APPROVED"`.
4. Otherwise, if `decision.decision == "ALLOW"`, execution is permitted.
5. The tool is resolved via `executor/tool_registry.py`.

Final `ExecutionResult` includes:

```python
@dataclass
class ExecutionResult:
    request_id: str
    success: bool
    executed: bool
    tool_name: str
    operation: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: Optional[str] = None
```

For a successful ALLOW path, `executed=True`, `success=True`, and `result` contains the mock tool result.

---

## 7. REQUIRE_APPROVAL -> approval -> execution flow

This is the approval path in the actual code.

The flow is:

1. Part 3 sets `decision.decision = "REQUIRE_APPROVAL"`
2. Part 3 provides `approval_id` and usually `approval_status`
3. Part 4 checks `decision.approval_status` in `execute_request()`
4. If `approval_status` is not `APPROVED`, execution is denied
5. If `approval_status == "APPROVED"`, the tool is executed

The exact decision logic is:

```python
if decision.decision == "REQUIRE_APPROVAL":
    if decision_state == "APPROVED":
        pass
    else:
        return ExecutionResult(... error="Execution blocked: approval is not approved")
```

This means PENDING and REJECTED are both blocked.

The approval record itself is managed by `AuditService`:

```python
AuditService.create_approval(...)
AuditService.get_approval(approval_id)
AuditService.resolve_approval(approval_id, status="APPROVED" | "REJECTED")
```

The database schema for approval records is in `database/schema.sql`:

```sql
CREATE TABLE approval_records (
    approval_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    status TEXT NOT NULL,
    approver_id TEXT,
    reason TEXT,
    resolved_at TEXT
);
```

Valid statuses in code are restricted to:

- `APPROVED`
- `REJECTED`

There is no runtime support for additional approval states in `AuditService.resolve_approval()`.

---

## 8. BLOCK -> no execution

The Block path is enforced before the tool registry is invoked.

```python
if decision.decision == "BLOCK":
    return ExecutionResult(
        request_id=proposed_action.request_id,
        success=False,
        executed=False,
        tool_name=proposed_action.tool_name,
        operation=proposed_action.operation,
        result=None,
        error="Execution blocked by authorization decision",
        executed_at=_now_iso(),
    )
```

This stays true even if `approval_status` is `APPROVED` or `PENDING`:

```python
Decision = BLOCK
        ↓
NEVER EXECUTE
```

The tests confirm this behavior:

- `tests/test_executor.py` includes `test_block_never_executes_even_if_approved()`
- it asserts `result.executed is False` and `result.error == "Execution blocked by authorization decision"`

The Part 4 design spec matches this rule: `BLOCK` cannot be overridden inside Part 4.

---

## 9. What Part 4 sends back to the dashboard/other parts

Part 4 sends back three main categories of data:

### 9.1 Execution result
`execute_request()` returns an `ExecutionResult` object.

Example payload:

```json
{
  "request_id": "uuid",
  "success": true,
  "executed": true,
  "tool_name": "crm",
  "operation": "update",
  "result": {
    "success": true
  },
  "error": null,
  "executed_at": "ISO8601"
}
```

This is the immediate execution status sent back to the caller or orchestrator.

### 9.2 Audit log records
Part 4 writes a lifecycle audit record using `AuditService.create_log()`.

Exact audit log schema from `audit/models.py` and `database/schema.sql`:

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

`AuditLog.to_dict()` returns this exact shape.

### 9.3 Execution records
Part 4 optionally stores per-tool execution details using `AuditService.record_execution()`.

Schema:

```json
{
  "execution_id": "uuid",
  "request_id": "uuid",
  "tool_name": "string",
  "operation": "string",
  "executed": true,
  "success": true,
  "result": "JSON string or null",
  "error": "string or null",
  "executed_at": "ISO8601"
}
```

This is separate from the lifecycle audit log and is designed for debugging and detailed execution tracing.

---

## 10. Audit Log output and how other parts can retrieve it

The official lifecycle audit record is created in `audit/service.py`:

```python
AuditService.create_log(
    proposed_action=proposed_action,
    decision=decision,
    executed=executed,
    resolved_at=resolved_at,
)
```

The repository writes to `audit_logs` in SQLite.

Retrieval methods currently implemented:

```python
AuditService.get_log(audit_log_id: str) -> Optional[AuditLog]
AuditService.get_log_by_request(request_id: str) -> Optional[AuditLog]
AuditService.list_logs(
    decision: Optional[str] = None,
    tool_name: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 200,
) -> List[AuditLog]
```

Query methods are backed by the repository:

- `get_audit_log_by_id()`
- `get_audit_log_by_request_id()`
- `list_audit_logs()`

This is the actual retrieval surface that other parts can use. There is no FastAPI route currently exposing these endpoints, so in the current code they are Python-level service calls rather than REST calls.

---

## 11. Required API endpoints/interfaces

The currently implemented FastAPI app is defined in `api/routes.py`.

### 11.1 Health endpoints

```python
@app.get("/health")
@app.get("/part4/health")
def health_check():
    return {
        "status": "healthy",
        "service": "sentinel-ai-part4",
        "attack_lab_available": True,
    }
```

### 11.2 Attack Simulation Lab endpoints

From `api/attack_routes.py`:

- `GET /part4/attacks`
- `GET /part4/attacks/{scenario}`
- `POST /part4/attacks/{scenario}/generate`
- `POST /part4/attacks/{scenario}/run`

Example request body for scenario generation or run:

```json
{
  "request_id": "optional-custom-id",
  "agent_id": "optional-custom-agent",
  "session_id": "optional-custom-session",
  "destination": "optional-destination",
  "query": "optional-sql-query",
  "target_resource": "optional-target-resource",
  "custom_prompt": "optional-custom-injection",
  "extra_context": {}
}
```

The response for generation is currently:

```json
{
  "scenario": "prompt_injection",
  "proposed_action": {
    "request_id": "...",
    "agent_id": "...",
    "session_id": "...",
    "timestamp": "...",
    "tool_name": "email",
    "operation": "send",
    "arguments": { ... },
    "target_resource": "...",
    "destination": "...",
    "context": { ... }
  }
}
```

The response for scenario execution (`/run`) includes:

```json
{
  "scenario": "prompt_injection",
  "status": "PIPELINE_EXECUTED",
  "message": "Attack simulation completed through Sentinel pipeline.",
  "proposed_action": { ... },
  "pipeline_executed": true,
  "pipeline_result": { ... }
}
```

If no pipeline runner is registered, it returns a `PROPOSED_ACTION_GENERATED` response instead.

### 11.3 Missing interfaces currently present in code

The code does not currently define any REST endpoints for:

- executing a proposed action against a decision
- retrieving a single audit log by `request_id`
- listing audit logs by dashboard
- resolving approval records via API
- exposing an approval queue endpoint

These capabilities exist in Python service code (`AuditService`, `execute_request`) but are not exposed as route handlers in the current app.

---

## 12. Expected request/response examples

### 12.1 Direct Python call

```python
from executor.executor import execute_request
from executor.model import ProposedAction, DecisionObject

proposed_action = ProposedAction(
    request_id="req-123",
    agent_id="agent-1",
    session_id="sess-1",
    timestamp="2026-09-11T12:00:00Z",
    tool_name="crm",
    operation="update",
    arguments={"status": "verified"},
    target_resource="customer_123",
    destination=None,
    context={"user_request": "Update customer status"},
)

decision = DecisionObject(
    request_id="req-123",
    decision="ALLOW",
    risk_score=20,
    risk_factors={"tool_sensitivity": 10},
    policy_rule_triggered=None,
    explanation="Allowed by policy",
    requires_human_approval=False,
    approval_id=None,
    timestamp="2026-09-11T12:00:01Z",
    audit_log_id="audit-123",
    approval_status=None,
)

result = execute_request(proposed_action, decision)
```

Expected result:

```json
{
  "request_id": "req-123",
  "success": true,
  "executed": true,
  "tool_name": "crm",
  "operation": "update",
  "result": { "success": true },
  "error": null,
  "executed_at": "ISO8601"
}
```

### 12.2 Block example

```python
decision = DecisionObject(
    request_id="req-456",
    decision="BLOCK",
    risk_score=90,
    risk_factors={"injection_signal": 95},
    explanation="Malicious behavior detected",
    requires_human_approval=False,
    approval_id=None,
    timestamp="2026-09-11T12:00:02Z",
    audit_log_id="audit-456",
)

result = execute_request(proposed_action, decision)
```

Expected result:

```json
{
  "request_id": "req-456",
  "success": false,
  "executed": false,
  "tool_name": "email",
  "operation": "send",
  "result": null,
  "error": "Execution blocked by authorization decision",
  "executed_at": "ISO8601"
}
```

### 12.3 Approval required example

```python
decision = DecisionObject(
    request_id="req-789",
    decision="REQUIRE_APPROVAL",
    risk_score=70,
    risk_factors={"destination_risk": 75},
    explanation="Requires human approval",
    requires_human_approval=True,
    approval_id="approval-789",
    timestamp="2026-09-11T12:00:03Z",
    audit_log_id="audit-789",
    approval_status="APPROVED",
)
```

If `approval_status` is `APPROVED`, the tool executes; if `PENDING` or `REJECTED`, execution is blocked.

---

## 13. What Parts 1–3 need to provide for integration

### Part 1 must provide

- a `ProposedAction` instance or equivalent JSON payload
- `request_id` that is unique per request
- `agent_id`
- `session_id`
- `timestamp`
- `tool_name`
- `operation`
- `arguments`
- `target_resource`
- `destination` if relevant
- `context.user_request`
- `context.untrusted_content_sources` when external content influenced the action

### Part 2 must provide

- risk-scored data that populates `DecisionObject.risk_score` and `DecisionObject.risk_factors`
- any policy or detection context needed by Part 3

### Part 3 must provide

- final `DecisionObject`
- `decision` in `ALLOW | REQUIRE_APPROVAL | BLOCK`
- matching `request_id`
- `risk_score` / `risk_factors`
- `timestamp`
- `audit_log_id` or allow Part 4 to generate one
- `approval_id` if approval is required
- `approval_status` if the current runtime decision is being evaluated in the Part 4 executor

### Required coordination rule

The matching `request_id` is mandatory across all objects.

If any part emits a request with a mismatched identifier, Part 4 blocks execution by design.

---

## 14. Mismatches and missing interfaces in the current code

There are a few important mismatches between the Part 4 design spec and the live code:

1. `DecisionObject` in code includes `approval_status`, but the original Part 4 spec does not list it as a required field.
   - This is not a problem for runtime logic, but it is an implementation extension outside the spec document.

2. The Part 4 spec describes a general dashboard and approval queue, but the current FastAPI app does not expose routes for:
   - execution approval
   - audit retrieval
   - approval retrieval
   - dashboard queries

3. The code has `AuditService` methods for approval record creation and resolution, but no dedicated API route is implemented for them.

4. The code expects `approval_status` on the `DecisionObject`, but the Part 4 design section mostly describes `approval_id` and `requires_human_approval`.
   - In practice, the executor reads `decision.approval_status`, not a separate approval object fetched via REST.

5. `api/execution_routes.py` and `api/audit_routes.py` are empty files.
   - This means there is no current public execution endpoint or audit endpoint in FastAPI even though the service layer is implemented.

6. `DecisionObject.audit_log_id` is optional in the dataclass, but the spec calls it required.
   - In practice, `AuditService.create_log()` will generate a new `audit_log_id` if one is not supplied.

These are the real integration gaps present in the code as implemented today.

---

## 15. Bottom line

The real integration path in this repository is:

```text
Part 1 -> ProposedAction
      -> Part 2 -> risk metadata
      -> Part 3 -> DecisionObject
      -> Part 4 -> execute_request(proposed_action, decision)
      -> execute tool only if request_id matches and decision allows it
      -> create AuditLog + ExecutionRecord
      -> return ExecutionResult to orchestrator/dashboard callers
```

The core integration contract is not a new invented interface. It is the actual repository contract already implemented in:

- `executor/model.py`
- `executor/executor.py`
- `audit/service.py`
- `database/schema.sql`
- `api/attack_routes.py`

This is the contract Part 4 actually honors today.
