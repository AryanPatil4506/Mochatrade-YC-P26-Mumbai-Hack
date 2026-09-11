"""Schema-only tool registry.

No tool implementations exist in the agent process (layer 1 of the
enforcement boundary in CLAUDE.md) — these are OpenAI function-calling
schemas used only to constrain what the LLM can *propose*. Actual execution
happens only in the executor service (Part 4), gated by the gateway
(Part 3). `TOOL_NAME_OPERATION_MAP` is the fixed mapping from a function
name the model picks to the (tool_name, operation) pair used everywhere
else — the model is never asked for tool_name/operation directly.
"""

from __future__ import annotations

from packages.contracts.enums import Operation, ToolName

TOOL_NAME_OPERATION_MAP: dict[str, tuple[ToolName, Operation]] = {
    "crm_read": (ToolName.CRM, Operation.READ),
    "crm_update": (ToolName.CRM, Operation.UPDATE),
    "ticketing_read": (ToolName.TICKETING, Operation.READ),
    "ticketing_update": (ToolName.TICKETING, Operation.UPDATE),
    "database_read": (ToolName.DATABASE, Operation.READ),
    "database_delete": (ToolName.DATABASE, Operation.DELETE),
    "email_send": (ToolName.EMAIL, Operation.SEND),
    "web_read": (ToolName.WEB, Operation.READ),
}

TOOL_FUNCTIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "crm_read",
            "description": "Read a CRM contact record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                },
                "required": ["contact_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_update",
            "description": "Update fields on a CRM contact record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "fields": {"type": "object"},
                },
                "required": ["contact_id", "fields"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ticketing_read",
            "description": "Read a support ticket.",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "string"}},
                "required": ["ticket_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ticketing_update",
            "description": "Update fields on a support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "fields": {"type": "object"},
                },
                "required": ["ticket_id", "fields"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "database_read",
            "description": "Run a read-only query against a database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "filter": {"type": "string"},
                },
                "required": ["table"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "database_delete",
            "description": "Delete rows from a database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "filter": {"type": "string"},
                },
                "required": ["table"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "email_send",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_read",
            "description": "Fetch a web page.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]
