from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class UntrustedContentSource(BaseModel):
    source: str = Field(..., description="email | ticket | web_page | database_record")
    content: str = Field(..., description="Content of the untrusted source")


class ActionContext(BaseModel):
    user_request: Optional[str] = Field(None, description="Original user prompt or task")
    untrusted_content_sources: List[UntrustedContentSource] = Field(
        default_factory=list,
        description="List of untrusted content sources encountered during execution"
    )


class ProposedAction(BaseModel):
    request_id: UUID = Field(..., description="Unique request UUID")
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    session_id: UUID = Field(..., description="Session UUID")
    timestamp: datetime = Field(..., description="ISO8601 timestamp")
    tool_name: str = Field(..., description="email | database | crm | ticketing | web")
    operation: str = Field(..., description="read | write | update | delete | send")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Operation arguments")
    target_resource: str = Field(..., min_length=1, description="Target resource or entity")
    destination: Optional[str] = Field(None, description="External or internal destination")
    context: Optional[ActionContext] = Field(default_factory=ActionContext, description="Execution context")

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        valid_tools = {"email", "database", "crm", "ticketing", "web"}
        clean = v.strip().lower()
        if clean not in valid_tools:
            # We allow it to be validated so security policy can also flag unknown tools,
            # but keep normalized lowercase.
            return clean
        return clean

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        return v.strip().lower()

    def model_dump_json_contract(self) -> dict:
        """Helper to serialize conforming to exact JSON contract types."""
        return {
            "request_id": str(self.request_id),
            "agent_id": self.agent_id,
            "session_id": str(self.session_id),
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "operation": self.operation,
            "arguments": self.arguments,
            "target_resource": self.target_resource,
            "destination": self.destination,
            "context": self.context.model_dump() if self.context else {"user_request": "", "untrusted_content_sources": []}
        }
