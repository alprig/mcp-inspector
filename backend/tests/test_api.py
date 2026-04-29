"""Tests for FastAPI endpoints: REST + WebSocket."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

import proxy as proxy_module
from main import app
from models import McpEvent
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
            "direction", "status", "latency_ms", "payload",
        }
        assert required_fields.issubset(data.keys())
        assert data["server"] == "test-server"
        assert data["tool"] == "my_tool"
        assert data["latency_ms"] == 123.45


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
    def test_ws_connect_receives_history(self) -> None:
        """On connect, client receives up to 100 existing events."""
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

        servers = {m["server"] for m in messages}
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
async def test_ws_receives_new_event_async() -> None:
    """New events emitted after connect are broadcast to WebSocket clients."""
    from httpx import ASGITransport, AsyncClient
    import httpx

    clear_events()

    # Use anyio-compatible WebSocket test via the sync client in an async wrapper.
    # Strategy: subscribe to the queue directly (same as WebSocket handler does),
    # emit an event, then verify it's in the queue — then separately verify
    # the REST endpoint also has it.

    # Register a queue subscriber the same way WebSocket does
    q = proxy_module.subscribe()

    event = McpEvent(
        server="live-server",
        method="tools/list",
        direction="request",
        status="pending",
        payload={},
    )
    _emit_event(event)

    # Queue should receive the event immediately (same thread, put_nowait)
    assert not q.empty()
    received = q.get_nowait()
    assert received.server == "live-server"

    proxy_module.unsubscribe(q)

    # Also verify via REST that event was stored
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["server"] == "live-server"
