"""Fixed tool dispatch — the only place tool names resolve to code. Nothing
outside services/executor/ can call these functions directly (structural
enforcement layer 1: no tool implementations exist in the agent process)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from services.executor.tools.crm import crm_execute
from services.executor.tools.database import database_execute
from services.executor.tools.email import email_execute
from services.executor.tools.ticketing import ticketing_execute
from services.executor.tools.web import web_execute

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
) -> dict:
    tool = get_tool(tool_name)
    if tool is None:
        raise ValueError(f"Tool '{tool_name}' is not allowed by the registry")
    return tool(
        operation=operation,
        arguments=arguments or {},
        target_resource=target_resource,
        destination=destination,
    )
