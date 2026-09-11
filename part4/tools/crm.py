from __future__ import annotations

from copy import deepcopy


_CUSTOMERS = {
    "customer_123": {"customer_id": "customer_123", "name": "Demo Customer", "email": "customer@example.test", "status": "active"},
    "customer_456": {"customer_id": "customer_456", "name": "Example Trading Co.", "email": "trading@example.test", "status": "pending"},
}
_CUSTOMER_FIELDS = {"name", "email", "status"}


def _failure(operation: object, message: str, target_resource: str | None, destination: str | None):
    return {"success": False, "simulated": True, "tool": "crm", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": None, "error": message}


def crm_execute(operation: str, arguments: dict | None = None, target_resource: str | None = None, destination: str | None = None):
    if arguments is None:
        arguments = {}
    operation = operation.lower() if isinstance(operation, str) else operation
    if operation not in {"read", "write", "update", "delete"}:
        return _failure(operation, "Unsupported CRM operation", target_resource, destination)
    if not isinstance(arguments, dict):
        return _failure(operation, "arguments must be an object", target_resource, destination)
    if operation == "read":
        customer = _CUSTOMERS.get(target_resource or arguments.get("customer_id"))
        if customer is None:
            return _failure(operation, "Customer was not found", target_resource, destination)
        result = {"customer": deepcopy(customer)}
    elif operation == "write":
        customer_id = target_resource or arguments.get("customer_id")
        if not isinstance(customer_id, str) or not customer_id or customer_id in _CUSTOMERS:
            return _failure(operation, "A new, unique customer_id is required", target_resource, destination)
        if not isinstance(arguments.get("name"), str) or not arguments["name"]:
            return _failure(operation, "name is required", target_resource, destination)
        customer = {"customer_id": customer_id, "name": arguments["name"], "email": arguments.get("email", ""), "status": arguments.get("status", "active")}
        _CUSTOMERS[customer_id] = customer
        result = {"customer": deepcopy(customer)}
    elif operation == "update":
        customer_id = target_resource or arguments.get("customer_id")
        customer = _CUSTOMERS.get(customer_id)
        updates = {key: value for key, value in arguments.items() if key != "customer_id"}
        if customer is None:
            return _failure(operation, "Customer was not found", target_resource, destination)
        if not updates or not set(updates).issubset(_CUSTOMER_FIELDS):
            return _failure(operation, "Only name, email, and status can be updated", target_resource, destination)
        customer.update(updates)
        result = {"customer": deepcopy(customer)}
    else:
        customer_id = target_resource or arguments.get("customer_id")
        if customer_id not in _CUSTOMERS:
            return _failure(operation, "Customer was not found", target_resource, destination)
        del _CUSTOMERS[customer_id]
        result = {"deleted_customer_id": customer_id}
    return {"success": True, "simulated": True, "tool": "crm", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": result, "error": None}


def reset_demo_data() -> None:
    _CUSTOMERS.clear()
    _CUSTOMERS.update({
        "customer_123": {"customer_id": "customer_123", "name": "Demo Customer", "email": "customer@example.test", "status": "active"},
        "customer_456": {"customer_id": "customer_456", "name": "Example Trading Co.", "email": "trading@example.test", "status": "pending"},
    })
