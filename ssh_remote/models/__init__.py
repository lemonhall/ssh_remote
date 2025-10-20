"""Data models for SSH Remote Assistant."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    """SSH authentication methods."""
    PASSWORD = "password"
    KEY = "key"


class CommandSource(str, Enum):
    """Source of command execution."""
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
    TEMPLATE = "template"


class Server(BaseModel):
    """SSH server configuration."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    host: str
    port: int = 22
    username: str
    auth_method: AuthMethod = AuthMethod.KEY
    key_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class CommandRecord(BaseModel):
    """Command execution record."""
    id: UUID = Field(default_factory=uuid4)
    server_id: UUID
    command: str
    output: str = ""
    exit_code: int = 0
    executed_at: datetime = Field(default_factory=datetime.now)
    source: CommandSource = CommandSource.MANUAL


class CommandTemplate(BaseModel):
    """Reusable command template."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    category: str = "general"
    commands: list[str]
    created_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    """Chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
