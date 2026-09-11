from __future__ import annotations

from copy import deepcopy


_TICKETS = {
    "TICKET-1001": {"ticket_id": "TICKET-1001", "title": "Demo ticket", "description": "Sandbox issue", "status": "open", "priority": "normal"},
    "TICKET-1002": {"ticket_id": "TICKET-1002", "title": "Example billing question", "description": "Demo billing data", "status": "pending", "priority": "low"},
    "TICKET-1003": {"ticket_id": "TICKET-1003", "title": "Sandbox incident", "description": "Demo incident", "status": "closed", "priority": "high"},
}
_TICKET_FIELDS = {"title", "description", "status", "priority"}


def _failure(operation: object, message: str, target_resource: str | None, destination: str | None):
    return {"success": False, "simulated": True, "tool": "ticketing", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": None, "error": message}


def ticketing_execute(operation: str, arguments: dict | None = None, target_resource: str | None = None, destination: str | None = None):
    if arguments is None:
        arguments = {}
    operation = operation.lower() if isinstance(operation, str) else operation
    if operation not in {"read", "write", "update", "delete"}:
        return _failure(operation, "Unsupported ticketing operation", target_resource, destination)
    if not isinstance(arguments, dict):
        return _failure(operation, "arguments must be an object", target_resource, destination)
    ticket_id = target_resource or arguments.get("ticket_id")
    if operation == "read":
        ticket = _TICKETS.get(ticket_id)
        if ticket is None:
            return _failure(operation, "Ticket was not found", target_resource, destination)
        result = {"ticket": deepcopy(ticket)}
    elif operation == "write":
        if not isinstance(ticket_id, str) or not ticket_id or ticket_id in _TICKETS:
            return _failure(operation, "A new, unique ticket_id is required", target_resource, destination)
        if not isinstance(arguments.get("title"), str) or not arguments["title"]:
            return _failure(operation, "title is required", target_resource, destination)
        ticket = {"ticket_id": ticket_id, "title": arguments["title"], "description": arguments.get("description", ""),
                  "status": arguments.get("status", "open"), "priority": arguments.get("priority", "normal")}
        _TICKETS[ticket_id] = ticket
        result = {"ticket": deepcopy(ticket)}
    elif operation == "update":
        ticket = _TICKETS.get(ticket_id)
        updates = {key: value for key, value in arguments.items() if key != "ticket_id"}
        if ticket is None:
            return _failure(operation, "Ticket was not found", target_resource, destination)
        if not updates or not set(updates).issubset(_TICKET_FIELDS):
            return _failure(operation, "Only title, description, status, and priority can be updated", target_resource, destination)
        ticket.update(updates)
        result = {"ticket": deepcopy(ticket)}
    else:
        if ticket_id not in _TICKETS:
            return _failure(operation, "Ticket was not found", target_resource, destination)
        del _TICKETS[ticket_id]
        result = {"deleted_ticket_id": ticket_id}
    return {"success": True, "simulated": True, "tool": "ticketing", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": result, "error": None}
