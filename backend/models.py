"""Pydantic models for MCP Inspector backend."""

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
import uuid


class McpEvent(BaseModel):
    """Represents a single MCP JSON-RPC event captured by the proxy."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    server: str
    tool: str | None = None
    method: str
    direction: Literal["request", "response"]
    status: Literal["success", "error", "pending"]
    latency_ms: float | None = None
    payload: dict


class McpServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None


class AppConfig(BaseModel):
    """Parsed application configuration."""

    mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)
