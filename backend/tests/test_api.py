"""Tests for FastAPI endpoints: REST + WebSocket."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

import proxy as proxy_module
from main import app
from models import McpEvent, WsMessage
from proxy import _emit_event, clear_events, event_store


@pytest.fixture(autouse=True)
def reset_events():
    """Clear events before each test."""
    clear_events()
    yield
    clear_events()


client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------


class TestGetEvents:
    def test_empty(self) -> None:
        resp = client.get("/events")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_events(self) -> None:
        event = McpEvent(
            server="srv",
            method="tools/list",
            direction="request",
            status="pending",
            payload={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        _emit_event(event)
        resp = client.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["server"] == "srv"
        assert data[0]["method"] == "tools/list"

    def test_limit_parameter(self) -> None:
        for i in range(10):
            _emit_event(
                McpEvent(
                    server="s",
                    method=f"m{i}",
                    direction="request",
                    status="pending",
                    payload={},
                )
            )
        resp = client.get("/events?limit=5")
        assert resp.status_code == 200
        assert len(resp.json()) == 5

    def test_event_fields_present(self) -> None:
        event = McpEvent(
            server="test-server",
            tool="my_tool",
            method="tools/call",
            direction="response",
            status="success",
            latency_ms=123.45,
            payload={"result": {}},
        )
        _emit_event(event)
        resp = client.get("/events")
        data = resp.json()[0]

        required_fields = {
            "id", "timestamp", "server", "tool", "method",
            "direction", "status", "latency_ms", "payload", "request_id",
        }
        assert required_fields.issubset(data.keys())
        assert data["server"] == "test-server"
        assert data["tool"] == "my_tool"
        assert data["latency_ms"] == 123.45

    def test_event_has_request_id_field(self) -> None:
        """GET /events returns events with request_id field."""
        event = McpEvent(
            server="srv",
            method="ping",
            direction="request",
            status="pending",
            payload={},
            request_id="7",
        )
        _emit_event(event)
        resp = client.get("/events")
        data = resp.json()[0]
        assert "request_id" in data
        assert data["request_id"] == "7"


# ---------------------------------------------------------------------------
# DELETE /events
# ---------------------------------------------------------------------------


class TestDeleteEvents:
    def test_clears_events(self) -> None:
        _emit_event(
            McpEvent(
                server="s",
                method="m",
                direction="request",
                status="pending",
                payload={},
            )
        )
        assert len(event_store) == 1

        resp = client.delete("/events")
        assert resp.status_code == 200
        assert resp.json() == {"status": "cleared"}
        assert len(event_store) == 0

    def test_delete_idempotent(self) -> None:
        resp = client.delete("/events")
        assert resp.status_code == 200
        resp2 = client.delete("/events")
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# WebSocket /ws — history tests (safe: events exist before connect)
# ---------------------------------------------------------------------------


class TestWebSocketHistory:
    def test_ws_connect_receives_history_as_ws_messages(self) -> None:
        """On connect, client receives history events wrapped in WsMessage with type='history'."""
        for i in range(5):
            _emit_event(
                McpEvent(
                    server=f"server-{i}",
                    method=f"method-{i}",
                    direction="request",
                    status="pending",
                    payload={"index": i},
                )
            )

        with client.websocket_connect("/ws") as ws:
            messages = []
            for _ in range(5):
                raw = ws.receive_text()
                messages.append(json.loads(raw))

        # Each message must have type="history" and nested event
        for msg in messages:
            assert "type" in msg, f"Missing 'type' field in message: {msg}"
            assert msg["type"] == "history"
            assert "event" in msg

        servers = {m["event"]["server"] for m in messages}
        assert servers == {f"server-{i}" for i in range(5)}

    def test_ws_ping_pong(self) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("ping")
            response = ws.receive_text()
            assert response == "pong"

    def test_ws_history_capped_at_100(self) -> None:
        """Client receives at most 100 historical events."""
        for i in range(150):
            _emit_event(
                McpEvent(
                    server="s",
                    method=f"m{i}",
                    direction="request",
                    status="pending",
                    payload={},
                )
            )

        with client.websocket_connect("/ws") as ws:
            messages = []
            for _ in range(100):
                raw = ws.receive_text()
                messages.append(json.loads(raw))

        assert len(messages) == 100
        # All messages should have type="history"
        for msg in messages:
            assert msg["type"] == "history"

    def test_ws_no_history_when_empty(self) -> None:
        """When no events exist, connect succeeds without sending anything."""
        with client.websocket_connect("/ws") as ws:
            ws.send_text("ping")
            response = ws.receive_text()
            assert response == "pong"


# ---------------------------------------------------------------------------
# WebSocket /ws — live streaming via async test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ws_receives_new_event_as_ws_message() -> None:
    """New events emitted after connect are broadcast as WsMessage objects."""
    from httpx import ASGITransport, AsyncClient

    clear_events()

    # Register a queue subscriber the same way WebSocket does
    q = proxy_module.subscribe()

    event = McpEvent(
        server="live-server",
        method="tools/list",
        direction="request",
        status="pending",
        payload={},
    )
    _emit_event(event, "event_created")

    # Queue should receive a WsMessage (not a bare McpEvent)
    assert not q.empty()
    ws_msg = q.get_nowait()
    assert isinstance(ws_msg, WsMessage)
    assert ws_msg.type == "event_created"
    assert ws_msg.event.server == "live-server"

    proxy_module.unsubscribe(q)

    # Also verify via REST that event was stored
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["server"] == "live-server"


@pytest.mark.asyncio
async def test_ws_event_updated_message() -> None:
    """event_updated type is broadcast when an event is mutated in-place."""
    from httpx import ASGITransport, AsyncClient

    clear_events()

    q = proxy_module.subscribe()

    # Emit an initial request event
    event = McpEvent(
        server="srv",
        method="ping",
        direction="request",
        status="pending",
        payload={},
    )
    _emit_event(event, "event_created")
    ws_msg1 = q.get_nowait()
    assert ws_msg1.type == "event_created"

    # Now broadcast an update for the same event
    from proxy import _broadcast
    event.status = "success"  # type: ignore[assignment]
    event.direction = "response"
    _broadcast(event, "event_updated")

    ws_msg2 = q.get_nowait()
    assert isinstance(ws_msg2, WsMessage)
    assert ws_msg2.type == "event_updated"
    assert ws_msg2.event.id == event.id

    proxy_module.unsubscribe(q)


# ---------------------------------------------------------------------------
# POST /replay/{event_id}
# ---------------------------------------------------------------------------


class TestReplayEndpoint:
    def test_replay_not_found(self) -> None:
        """Returns 404 when event_id does not exist in the store."""
        resp = client.post("/replay/nonexistent-id-000")
        assert resp.status_code == 404
        assert "Event not found" in resp.json()["detail"]

    def test_replay_response_event(self) -> None:
        """Returns 400 when the event is a response (cannot replay responses)."""
        event = McpEvent(
            server="srv",
            method="tools/list",
            direction="response",
            status="success",
            payload={"jsonrpc": "2.0", "id": 1, "result": {}},
        )
        _emit_event(event)
        resp = client.post(f"/replay/{event.id}")
        assert resp.status_code == 400
        assert "Can only replay request events" in resp.json()["detail"]

    def test_replay_no_proxy(self) -> None:
        """Returns 503 when the proxy for the event's server is not running."""
        event = McpEvent(
            server="ghost-server",
            method="tools/list",
            direction="request",
            status="pending",
            payload={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        _emit_event(event)
        # No proxy registered for "ghost-server" in module-level manager
        resp = client.post(f"/replay/{event.id}")
        assert resp.status_code == 503
        assert "ghost-server" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_replay_success(self) -> None:
        """Returns 200 with ok=True and a new event_id when replay succeeds."""
        # Create the original request event
        original = McpEvent(
            server="mock-server",
            method="tools/list",
            direction="request",
            status="pending",
            payload={"jsonrpc": "2.0", "id": 42, "method": "tools/list"},
        )
        _emit_event(original)

        # Build a mock proxy that is "running" and accepts send_request
        mock_proxy = MagicMock()
        mock_proxy.is_running = True
        mock_proxy.send_request = AsyncMock(side_effect=lambda data: _emit_event(
            McpEvent(
                server="mock-server",
                method="tools/list",
                direction="request",
                status="pending",
                payload={"jsonrpc": "2.0", "id": 43, "method": "tools/list"},
                replayed=True,
            )
        ))

        # Register mock proxy in the module-level manager
        proxy_module.manager._proxies["mock-server"] = mock_proxy

        try:
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(f"/replay/{original.id}")

            assert resp.status_code == 200
            body = resp.json()
            assert body["ok"] is True
            assert "event_id" in body
            # send_request was called once with the original payload bytes
            mock_proxy.send_request.assert_called_once()
        finally:
            proxy_module.manager._proxies.pop("mock-server", None)
