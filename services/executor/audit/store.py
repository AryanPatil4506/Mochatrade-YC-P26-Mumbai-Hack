"""Shared SQLite connection for the executor's audit/approval/token tables.

One file (default: repo root `sentinel.db`) is opened by both the gateway
process (to create audit rows and approval records at decision time) and the
executor process (to update them at execution time, and to check capability
token replay). This is a plain-file, in-process-friendly choice appropriate
for the "SQLite, no Postgres" constraint in CLAUDE.md; both sides only ever
touch this module, never each other's memory.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

_SCHEMA = Path(__file__).with_name("schema.sql").read_text()

_local = threading.local()


def _db_path() -> str:
    return os.environ.get("SENTINEL_DB_PATH", str(Path(__file__).resolve().parents[3] / "sentinel.db"))


def get_connection() -> sqlite3.Connection:
    path = _db_path()
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != path:
        conn = sqlite3.connect(path, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA)
        conn.commit()
        _local.conn = conn
        _local.path = path
    return conn


def close_connection() -> None:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
