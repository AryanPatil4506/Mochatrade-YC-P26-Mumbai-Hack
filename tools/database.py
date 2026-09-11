from __future__ import annotations

import sqlite3
from threading import Lock


_LOCK = Lock()
_CONNECTION = sqlite3.connect(":memory:", check_same_thread=False)
_CONNECTION.row_factory = sqlite3.Row
_CONNECTION.executescript("""
CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE trades (id TEXT PRIMARY KEY, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL, side TEXT NOT NULL);
CREATE TABLE accounts (id TEXT PRIMARY KEY, owner TEXT NOT NULL, balance REAL NOT NULL);
CREATE TABLE transactions (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, amount REAL NOT NULL, kind TEXT NOT NULL);
CREATE TABLE tickets (id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL);
INSERT INTO customers VALUES ('customer_123', 'Demo Customer', 'customer@example.test', 'active');
INSERT INTO trades VALUES ('trade_1', 'MCH', 10, 125.50, 'buy');
INSERT INTO accounts VALUES ('account_1', 'Demo Customer', 10000.00);
INSERT INTO tickets VALUES ('TICKET-1001', 'Demo ticket', 'open');
""")
_CONNECTION.commit()


def _failure(operation: object, message: str, target_resource: str | None, destination: str | None):
    return {"success": False, "simulated": True, "tool": "database", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": None, "error": message}


def database_execute(operation: str, arguments: dict | None = None, target_resource: str | None = None, destination: str | None = None):
    if arguments is None:
        arguments = {}
    operation = operation.lower() if isinstance(operation, str) else operation
    aliases = {"read": "select", "write": "insert"}
    sql_operation = aliases.get(operation, operation)
    if sql_operation not in {"select", "insert", "update", "delete"}:
        return _failure(operation, "Unsupported database operation", target_resource, destination)
    if not isinstance(arguments, dict) or not isinstance(arguments.get("query"), str) or not arguments["query"].strip():
        return _failure(operation, "query is required", target_resource, destination)
    query = arguments["query"].strip()
    first_keyword = query.split(None, 1)[0].lower().rstrip(";")
    if first_keyword != sql_operation:
        return _failure(operation, f"Operation does not match SQL statement ({sql_operation})", target_resource, destination)
    if first_keyword in {"insert", "update", "delete"} and ";" in query.rstrip(";"):
        return _failure(operation, "Only one SQL statement is allowed", target_resource, destination)
    parameters = arguments.get("parameters", arguments.get("params", ()))
    try:
        with _LOCK:
            cursor = _CONNECTION.execute(query, parameters)
            if sql_operation == "select":
                rows = [dict(row) for row in cursor.fetchall()]
                result = {"rows": rows, "row_count": len(rows)}
            else:
                _CONNECTION.commit()
                result = {"row_count": cursor.rowcount, "lastrowid": cursor.lastrowid}
    except (sqlite3.Error, TypeError, ValueError) as exc:
        return _failure(operation, f"Sandbox SQL error: {exc}", target_resource, destination)
    return {"success": True, "simulated": True, "tool": "database", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": result, "error": None}


def reset_sandbox() -> None:
    with _LOCK:
        for table in ("customers", "trades", "accounts", "transactions", "tickets"):
            _CONNECTION.execute(f"DELETE FROM {table}")
        _CONNECTION.execute("INSERT INTO customers VALUES ('customer_123', 'Demo Customer', 'customer@example.test', 'active')")
        _CONNECTION.execute("INSERT INTO trades VALUES ('trade_1', 'MCH', 10, 125.50, 'buy')")
        _CONNECTION.execute("INSERT INTO accounts VALUES ('account_1', 'Demo Customer', 10000.00)")
        _CONNECTION.execute("INSERT INTO tickets VALUES ('TICKET-1001', 'Demo ticket', 'open')")
        _CONNECTION.commit()
