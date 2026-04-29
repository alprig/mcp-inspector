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
from models import McpEvent, McpServerConfig, WsMessage
from proxy import (
    McpProxy,
    ProxyManager,
    _emit_event,
    _pending_requests,
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

    def test_request_id_field(self) -> None:
        event = McpEvent(
            server="test",
            method="tools/list",
            direction="request",
            status="pending",
            payload={},
            request_id="42",
        )
        assert event.request_id == "42"

    def test_request_id_defaults_to_none(self) -> None:
        event = McpEvent(
            server="test",
            method="tools/list",
            direction="request",
            status="pending",
            payload={},
        )
        assert event.request_id is None

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


class TestWsMessage:
    def test_event_created_type(self) -> None:
        event = McpEvent(
            server="s",
            method="m",
            direction="request",
            status="pending",
            payload={},
        )
        msg = WsMessage(type="event_created", event=event)
        assert msg.type == "event_created"
        assert msg.event is event

    def test_event_updated_type(self) -> None:
        event = McpEvent(
            server="s",
            method="m",
            direction="response",
            status="success",
            payload={},
        )
        msg = WsMessage(type="event_updated", event=event)
        assert msg.type == "event_updated"

    def test_history_type(self) -> None:
        event = McpEvent(
            server="s",
            method="m",
            direction="request",
            status="pending",
            payload={},
        )
        msg = WsMessage(type="history", event=event)
        assert msg.type == "history"

    def test_model_dump_json_has_type_field(self) -> None:
        event = McpEvent(
            server="srv",
            method="ping",
            direction="request",
            status="pending",
            payload={},
        )
        msg = WsMessage(type="event_created", event=event)
        parsed = json.loads(msg.model_dump_json())
        assert "type" in parsed
        assert parsed["type"] == "event_created"
        assert "event" in parsed
        assert parsed["event"]["server"] == "srv"


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

    def test_subscriber_queue_receives_ws_message(self) -> None:
        """Subscriber queues now receive WsMessage objects, not bare McpEvent."""
        q = subscribe()
        event = McpEvent(
            server="s",
            method="m",
            direction="response",
            status="success",
            payload={},
        )
        _emit_event(event, "event_created")
        assert not q.empty()
        ws_msg = q.get_nowait()
        assert isinstance(ws_msg, WsMessage)
        assert ws_msg.type == "event_created"
        assert ws_msg.event is event
        unsubscribe(q)

    def test_emit_event_updated_type(self) -> None:
        """event_updated type is correctly set on WsMessage."""
        q = subscribe()
        event = McpEvent(
            server="s",
            method="m",
            direction="response",
            status="success",
            payload={},
        )
        _emit_event(event, "event_updated")
        ws_msg = q.get_nowait()
        assert ws_msg.type == "event_updated"
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
# event pairing tests
# ---------------------------------------------------------------------------


class TestEventPairing:
    def setup_method(self) -> None:
        clear_events()

    @pytest.mark.asyncio
    async def test_request_creates_event_and_response_updates_it(self) -> None:
        """Sending request creates event_created; response updates same event."""
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()

        q = subscribe()

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
        await proxy.send_request(request.encode())

        # First message should be event_created
        ws_msg1 = q.get_nowait()
        assert isinstance(ws_msg1, WsMessage)
        assert ws_msg1.type == "event_created"
        assert ws_msg1.event.status == "pending"
        assert ws_msg1.event.direction == "request"
        assert ws_msg1.event.request_id == "1"
        event_id = ws_msg1.event.id

        # Simulate a response from the server
        response = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}})
        proxy._handle_response(response.encode())

        # Second message should be event_updated for the SAME event
        ws_msg2 = q.get_nowait()
        assert isinstance(ws_msg2, WsMessage)
        assert ws_msg2.type == "event_updated"
        assert ws_msg2.event.id == event_id  # same event, not a new one
        assert ws_msg2.event.status == "success"
        assert ws_msg2.event.direction == "response"

        # Only one event in store (not two)
        assert len(event_store) == 1

        unsubscribe(q)
        await proxy.stop()

    @pytest.mark.asyncio
    async def test_response_error_updates_status(self) -> None:
        """Error response updates event status to 'error'."""
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()

        q = subscribe()

        request = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {}})
        await proxy.send_request(request.encode())

        ws_msg1 = q.get_nowait()
        event_id = ws_msg1.event.id

        response = json.dumps({"jsonrpc": "2.0", "id": 2, "error": {"code": -1, "message": "fail"}})
        proxy._handle_response(response.encode())

        ws_msg2 = q.get_nowait()
        assert ws_msg2.type == "event_updated"
        assert ws_msg2.event.id == event_id
        assert ws_msg2.event.status == "error"

        assert len(event_store) == 1

        unsubscribe(q)
        await proxy.stop()

    @pytest.mark.asyncio
    async def test_response_without_matching_request_creates_new_event(self) -> None:
        """Response with unknown id creates a new standalone event."""
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()

        q = subscribe()

        # Simulate orphan response (no prior request in store)
        response = json.dumps({"jsonrpc": "2.0", "id": 99, "result": {}})
        proxy._handle_response(response.encode())

        ws_msg = q.get_nowait()
        assert ws_msg.type == "event_created"

        unsubscribe(q)
        await proxy.stop()


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
        """Sending a JSON-RPC request emits an event_created WsMessage."""
        clear_events()
        cfg = McpServerConfig(command="cat", args=[])
        proxy = McpProxy("cat-server", cfg)
        await proxy.start()

        q = subscribe()
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
        await proxy.send_request(request.encode())

        ws_msg = q.get_nowait()
        assert ws_msg.type == "event_created"
        assert ws_msg.event.method == "ping"
        assert ws_msg.event.direction == "request"

        unsubscribe(q)
        await proxy.stop()

        assert any(e.method == "ping" and e.direction == "request" for e in event_store)
