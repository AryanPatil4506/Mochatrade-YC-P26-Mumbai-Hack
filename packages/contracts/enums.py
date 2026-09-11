"""Enumerations shared across all four parts of Sentinel. Frozen — see CLAUDE.md."""

from enum import Enum


class ToolName(str, Enum):
    EMAIL = "email"
    DATABASE = "database"
    CRM = "crm"
    TICKETING = "ticketing"
    WEB = "web"


class Operation(str, Enum):
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    SEND = "send"


class DecisionValue(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TaintSource(str, Enum):
    EMAIL = "email"
    TICKET = "ticket"
    WEB_PAGE = "web_page"
    DATABASE_RECORD = "database_record"


class DetectorMode(str, Enum):
    RULES_AND_CLASSIFIER = "rules+classifier"
    RULES_ONLY = "rules_only"
