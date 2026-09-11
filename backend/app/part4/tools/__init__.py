from .crm import crm_execute
from .database import database_execute
from .email import email_execute
from .ticketing import ticketing_execute
from .web import web_execute

__all__ = [
    "crm_execute",
    "database_execute",
    "email_execute",
    "ticketing_execute",
    "web_execute",
]
