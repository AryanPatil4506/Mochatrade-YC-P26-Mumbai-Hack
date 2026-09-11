from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.part3.database.database import Base


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    permissions = relationship("Permission", back_populates="agent", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(64), ForeignKey("agents.agent_id"), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False)
    operation = Column(String(64), nullable=False)

    agent = relationship("Agent", back_populates="permissions")
