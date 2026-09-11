from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

_SCHEMA = Path(__file__).with_name("schema.sql").read_text()

_local = threading.local()


def _db_path() -> str:
    import os
    return os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "sentinel.db"))


def get_connection() -> sqlite3.Connection:
    path = _db_path()
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA)
        conn.commit()
        _local.conn = conn
    return _local.conn


def close_connection() -> None:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None


def init_db(path: str | None = None) -> None:
    import os
    if path:
        os.environ["DB_PATH"] = path
    close_connection()
    get_connection()
