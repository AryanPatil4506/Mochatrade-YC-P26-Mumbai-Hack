from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProposedAction:
    request_id: str
    agent_id: str
    session_id: str
    timestamp: str
    tool_name: str
    operation: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    target_resource: Optional[str] = None
    destination: Optional[str] = None
    context: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DecisionObject:
    request_id: str
    decision: str
    risk_score: float = 0
    risk_factors: Dict[str, Any] = field(default_factory=dict)
    policy_rule_triggered: Optional[str] = None
    explanation: str = ""
    requires_human_approval: bool = False
    approval_id: Optional[str] = None
    timestamp: str = ""
    audit_log_id: Optional[str] = None
    approval_status: Optional[str] = None


@dataclass
class ExecutionResult:
    request_id: str
    success: bool
    executed: bool
    tool_name: str
    operation: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: Optional[str] = None
