-- Sentinel AI -- Executor (Part 4) SQLite schema.
-- audit_logs / approval_records match the frozen AuditLogEntry / ApprovalRecord
-- contracts in packages/contracts/schemas.py field-for-field. Table internals
-- beyond those fields are free to change.

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_log_id  TEXT PRIMARY KEY,
    request_id    TEXT NOT NULL,
    agent_id      TEXT NOT NULL,
    tool_name     TEXT NOT NULL,
    operation     TEXT NOT NULL,
    risk_score    INTEGER NOT NULL,
    decision      TEXT NOT NULL,
    approval_id   TEXT,
    executed      BOOLEAN NOT NULL,
    created_at    TEXT NOT NULL,
    resolved_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_request  ON audit_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_logs(decision);
CREATE INDEX IF NOT EXISTS idx_audit_created  ON audit_logs(created_at);

-- action_json/risk_factors_json are executor-internal storage, not part of the
-- frozen ApprovalRecord wire contract: they let /v1/approvals/{id}/resolve
-- reissue a capability token bound to the original arguments after a process
-- restart, and let the dashboard show what it's approving.
CREATE TABLE IF NOT EXISTS approval_records (
    approval_id       TEXT PRIMARY KEY,
    request_id        TEXT NOT NULL,
    status            TEXT NOT NULL,
    approver_id       TEXT,
    reason            TEXT,
    resolved_at       TEXT,
    created_at        TEXT NOT NULL,
    action_json       TEXT NOT NULL,
    risk_score        INTEGER,
    risk_factors_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_approval_request ON approval_records(request_id);

CREATE TABLE IF NOT EXISTS execution_records (
    execution_id TEXT PRIMARY KEY,
    request_id   TEXT NOT NULL,
    tool_name    TEXT NOT NULL,
    operation    TEXT NOT NULL,
    executed     BOOLEAN NOT NULL,
    success      BOOLEAN NOT NULL,
    result       TEXT,
    error        TEXT,
    executed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_exec_request ON execution_records(request_id);

-- Single-use capability token replay guard (Enforcement Boundary layer 3).
CREATE TABLE IF NOT EXISTS used_tokens (
    jti     TEXT PRIMARY KEY,
    used_at TEXT NOT NULL
);
