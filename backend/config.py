"""Configuration loader: reads ~/.claude/settings.json → mcpServers."""

import json
import os
from pathlib import Path

from models import AppConfig, McpServerConfig


def get_settings_path() -> Path:
    """Return path to Claude settings.json."""
    return Path.home() / ".claude" / "settings.json"


def load_config(settings_path: Path | None = None) -> AppConfig:
    """Load MCP server configurations from Claude settings.json.

    Args:
        settings_path: Override path to settings.json (used in tests).

    Returns:
        AppConfig with parsed mcpServers.
    """
    path = settings_path or get_settings_path()

    if not path.exists():
        return AppConfig()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return AppConfig()

    raw_servers: dict = data.get("mcpServers", {})
    servers: dict[str, McpServerConfig] = {}

    for name, cfg in raw_servers.items():
        if not isinstance(cfg, dict):
            continue
        command = cfg.get("command", "")
        if not command:
            continue
        servers[name] = McpServerConfig(
            command=command,
            args=cfg.get("args", []),
            env=cfg.get("env") or None,
        )

    return AppConfig(mcp_servers=servers)
