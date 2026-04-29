"""Tests for proxy.py and config.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from models import McpEvent, McpServerConfig
from proxy import (
    McpProxy,
    ProxyManager,
    _emit_event,
    clear_events,
    event_store,
    subscribe,
    unsubscribe,
)


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_missing_file_returns_empty_config(self, tmp_path: Path) -> None:
        cfg = load_config(tmp_path / "nonexistent.json")
        assert cfg.mcp_servers == {}

    def test_invalid_json_returns_empty_config(self, tmp_path: Path) -> None:
        f = tmp_path / "settings.json"
        f.write_text("not json")
        cfg = load_config(f)
        assert cfg.mcp_servers == {}

    def test_empty_mcp_servers(self, tmp_path: Path) -> None:
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({"mcpServers": {}}))
        cfg = load_config(f)
        assert cfg.mcp_servers == {}

    def test_parses_mcp_servers(self, tmp_path: Path) -> None:
        data = {
            "mcpServers": {
                "myserver": {
                    "command": "node",
                    "args": ["server.js"],
                    "env": {"DEBUG": "1"},
                }
            }
        }
        f = tmp_path / "settings.json"
        f.write_text(json.dumps(data))
        cfg = load_config(f)
        assert "myserver" in cfg.mcp_servers
        srv = cfg.mcp_servers["myserver"]
        assert srv.command == "node"
        assert srv.args == ["server.js"]
        assert srv.env == {"DEBUG": "1"}

    def test_skips_server_without_command(self, tmp_path: Path) -> None:
        data = {"mcpServers": {"bad": {"args": []}}}
        f = tmp_path / "settings.json"
        f.write_text(json.dumps(data))
        cfg = load_config(f)
        assert cfg.mcp_servers == {}

    def test_ignores_extra_top_level_keys(self, tmp_path: Path) -> None:
        data = {"permissions": {"allow": []}, "mcpServers": {}}
        f = tmp_path / "settings.json"
        f.write_text(json.dumps(data))
        cfg = load_config(f)
        assert cfg.mcp_servers == {}


# ---------------------------------------------------------------------------
# models tests
# ---------------------------------------------------------------------------


class TestMcpEvent:
    def test_default_id_and_timestamp(self) -> None:
        event = McpEvent(
            server="test",
            method="tools/list",
            direction="request",
            status="pending",
            payload={},
        )
        assert event.id != ""
        assert isinstance(event.timestamp, datetime)

    def test_optional_fields(self) -> None:
        event = McpEvent(
            server="s",
            method="m",
            direction="response",
            status="success",
            payload={"result": "ok"},
            tool="my_tool",
            latency_ms=42.5,
        )
        assert event.tool == "my_tool"
        assert event.latency_ms == 42.5

    def test_model_dump_json_roundtrip(self) -> None:
        event = McpEvent(
            server="srv",
            method="ping",
            direction="request",
            status="pending",
            payload={"id": 1},
        )
        serialized = event.model_dump_json()
        parsed = json.loads(serialized)
        assert parsed["server"] == "srv"
        assert parsed["method"] == "ping"


# ---------------------------------------------------------------------------
# event store tests
# ---------------------------------------------------------------------------


class TestEventStore:
    def setup_method(self) -> None:
        clear_events()

    def test_clear_events(self) -> None:
        event = McpEvent(
            server="s",
            method="m",
            direction="request",
            status="pending",
            payload={},
        )
        _emit_event(event)
        assert len(event_store) == 1
        clear_events()
        assert len(event_store) == 0

    def test_emit_event_stores(self) -> None:
        event = McpEvent(
            server="test-server",
            method="tools/call",
            direction="request",
            status="pending",
            payload={"method": "tools/call"},
        )
        _emit_event(event)
        assert event in event_store

    def test_subscriber_queue_receives_event(self) -> None:
        q = subscribe()
        event = McpEvent(
            server="s",
            method="m",
            direction="response",
            status="success",
            payload={},
        )
        _emit_event(event)
        assert not q.empty()
        assert q.get_nowait() is event
        unsubscribe(q)

    def test_unsubscribe_stops_delivery(self) -> None:
        q = subscribe()
        unsubscribe(q)
        _emit_event(
            McpEvent(
                server="s",
                method="m",
                direction="request",
                status="pending",
                payload={},
            )
        )
        assert q.empty()


# ---------------------------------------------------------------------------
# proxy manager tests
# ---------------------------------------------------------------------------


class TestProxyManager:
    def test_add_and_get_proxy(self) -> None:
        mgr = ProxyManager()
        cfg = McpServerConfig(command="echo", args=["hello"])
        proxy = mgr.add_proxy("echo-server", cfg)
        assert mgr.get_proxy("echo-server") is proxy
        assert "echo-server" in mgr.proxies

    def test_get_nonexistent_proxy(self) -> None:
        mgr = ProxyManager()
        assert mgr.get_proxy("nope") is None


# ---------------------------------------------------------------------------
# McpProxy unit tests
# ---------------------------------------------------------------------------


class TestMcpProxy:
    def test_proxy_not_running_initially(self) -> None:
        cfg = McpServerConfig(command="echo")
        proxy = McpProxy("test", cfg)
        assert not proxy.is_running

    @pytest.mark.asyncio
    async def test_proxy_start_stop(self) -> None:
        """Test that a real subprocess can be started and stopped."""
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()
        assert proxy.is_running
        await proxy.stop()
        assert not proxy.is_running

    @pytest.mark.asyncio
    async def test_send_request_emits_event(self) -> None:
        """Sending a JSON-RPC request emits an event to the store."""
        clear_events()
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
        await proxy.send_request(request.encode())

        await proxy.stop()
        assert any(e.method == "ping" and e.direction == "request" for e in event_store)
