from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from tools.crm import crm_execute
from tools.database import database_execute
from tools.email import email_execute
from tools.ticketing import ticketing_execute
from tools.web import web_execute


TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "crm": crm_execute,
    "database": database_execute,
    "email": email_execute,
    "ticketing": ticketing_execute,
    "web": web_execute,
}


def get_tool(tool_name: str) -> Optional[Callable[..., Any]]:
    if tool_name is None:
        return None
    return TOOL_REGISTRY.get(str(tool_name).lower())


def execute_tool(
    tool_name: str,
    operation: str,
    arguments: Optional[dict] = None,
    target_resource: Optional[str] = None,
    destination: Optional[str] = None,
):
    tool = get_tool(tool_name)
    if tool is None:
        raise ValueError(f"Tool '{tool_name}' is not allowed by the registry")
    return tool(
        operation=operation,
        arguments=arguments or {},
        target_resource=target_resource,
        destination=destination,
    )
