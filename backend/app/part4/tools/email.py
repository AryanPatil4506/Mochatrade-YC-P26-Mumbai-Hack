from __future__ import annotations

from copy import deepcopy


_MESSAGES = {}
_NEXT_MESSAGE_ID = 1


def _failure(operation: object, message: str, target_resource: str | None, destination: str | None):
    return {"success": False, "simulated": True, "tool": "email", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": None, "error": message}


def email_execute(operation: str, arguments: dict | None = None, target_resource: str | None = None, destination: str | None = None):
    global _NEXT_MESSAGE_ID
    if arguments is None:
        arguments = {}
    operation = operation.lower() if isinstance(operation, str) else operation
    if operation not in {"send", "read"}:
        return _failure(operation, "Unsupported email operation", target_resource, destination)
    if not isinstance(arguments, dict):
        return _failure(operation, "arguments must be an object", target_resource, destination)
    if operation == "send":
        recipient = destination or arguments.get("recipient")
        subject = arguments.get("subject")
        body = arguments.get("body")
        if not isinstance(recipient, str) or not recipient.strip():
            return _failure(operation, "recipient is required", target_resource, destination)
        if not isinstance(subject, str) or not subject.strip() or not isinstance(body, str) or not body.strip():
            return _failure(operation, "subject and body are required", target_resource, destination)
        message_id = f"message-{_NEXT_MESSAGE_ID}"
        _NEXT_MESSAGE_ID += 1
        message = {"message_id": message_id, "recipient": recipient, "subject": subject, "body": body}
        _MESSAGES[message_id] = message
        result = {"message": "Email simulated successfully", "email": deepcopy(message)}
    else:
        message_id = target_resource or arguments.get("message_id")
        message = _MESSAGES.get(message_id)
        if message is None:
            return _failure(operation, "Message was not found", target_resource, destination)
        result = {"email": deepcopy(message)}
    return {"success": True, "simulated": True, "tool": "email", "operation": operation,
            "target_resource": target_resource, "destination": destination, "result": result, "error": None}


def reset_demo_data() -> None:
    global _NEXT_MESSAGE_ID
    _MESSAGES.clear()
    _NEXT_MESSAGE_ID = 1
