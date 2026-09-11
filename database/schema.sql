-- Sentinel AI -- Part 4 SQLite Schema
-- Exact field names as specified in PART4.md ss23-25. DO NOT CHANGE.

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

CREATE TABLE IF NOT EXISTS approval_records (
    approval_id  TEXT PRIMARY KEY,
    request_id   TEXT NOT NULL,
    status       TEXT NOT NULL,
    approver_id  TEXT,
    reason       TEXT,
    resolved_at  TEXT
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
