"""Tests for wrap.py: _derive_name unit tests + async integration test."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from wrap import _derive_name, run_wrap


# ---------------------------------------------------------------------------
# Unit tests for _derive_name
# ---------------------------------------------------------------------------


def test_derive_name_filesystem_server():
    assert (
        _derive_name(["npx", "@modelcontextprotocol/server-filesystem", "/path"])
        == "server-filesystem"
    )


def test_derive_name_python_script():
    assert _derive_name(["python", "my_server.py"]) == "my_server"


def test_derive_name_node_js():
    assert _derive_name(["node", "server.js"]) == "server"


def test_derive_name_simple_command():
    assert _derive_name(["my-server"]) == "my-server"


def test_derive_name_uvx():
    assert _derive_name(["uvx", "mcp-server-fetch"]) == "mcp-server-fetch"


def test_derive_name_python3_script():
    assert _derive_name(["python3", "my_server.py"]) == "my_server"


# ---------------------------------------------------------------------------
# Mock HTTP server (runs in a thread, records POSTed events)
# ---------------------------------------------------------------------------


class _RecordingHandler(BaseHTTPRequestHandler):
    """HTTP handler that records POSTed JSON bodies."""

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
        self.server.recorded_events.append(payload)  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"id":"mock"}')

    def log_message(self, *args, **kwargs):  # silence request logs in tests
        pass


class MockIngestServer:
    """Context manager: starts a local HTTP server on an ephemeral port."""

    def __init__(self):
        self.server: HTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.recorded_events: list[dict] = []

    @property
    def url(self) -> str:
        assert self.server is not None
        host, port = self.server.server_address
        return f"http://127.0.0.1:{port}"

    def __enter__(self) -> "MockIngestServer":
        self.server = HTTPServer(("127.0.0.1", 0), _RecordingHandler)
        self.server.recorded_events = self.recorded_events  # type: ignore[attr-defined]
        self.server.timeout = 0.1
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        return self

    def _serve(self) -> None:
        assert self.server is not None
        while not getattr(self.server, "_stop", False):
            self.server.handle_request()

    def __exit__(self, *_) -> None:
        if self.server:
            self.server._stop = True  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

# A minimal "echo MCP server": reads one JSON-RPC request, writes a response.
_ECHO_SCRIPT = """
import sys, json
line = sys.stdin.readline()
try:
    msg = json.loads(line)
except Exception:
    msg = {}
req_id = msg.get("id")
response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
sys.stdout.write(json.dumps(response) + "\\n")
sys.stdout.flush()
"""


@pytest.mark.asyncio
async def test_run_wrap_posts_events_to_ingest():
    """run_wrap posts request + response events to the mock /ingest endpoint."""
    import os

    with MockIngestServer() as mock:
        api_url = mock.url

        # We'll feed one JSON-RPC request via a pipe that substitutes stdin.
        request_msg = {"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}}
        request_bytes = json.dumps(request_msg).encode() + b"\n"

        read_fd, write_fd = os.pipe()

        # Write the request + EOF so handle_stdin terminates naturally
        os.write(write_fd, request_bytes)
        os.close(write_fd)

        original_stdin = sys.stdin
        # Replace sys.stdin.buffer with a readable file object backed by read_fd
        read_file = os.fdopen(read_fd, "rb", buffering=0)
        sys.stdin = type("_FakeStdin", (), {"buffer": read_file})()  # type: ignore

        try:
            await asyncio.wait_for(
                run_wrap("test-server", [sys.executable, "-c", _ECHO_SCRIPT], api_url=api_url),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("run_wrap did not finish within timeout")
        finally:
            sys.stdin = original_stdin
            read_file.close()

        # Give mock server a moment to record remaining requests
        await asyncio.sleep(0.1)

        # We expect at least one event (request), possibly two (request + response)
        assert len(mock.recorded_events) >= 1, (
            f"Expected at least 1 POSTed event, got {len(mock.recorded_events)}"
        )

        directions = [e.get("direction") for e in mock.recorded_events]
        assert "request" in directions, f"No request event found. Events: {mock.recorded_events}"

        # Check request event fields
        req_event = next(e for e in mock.recorded_events if e.get("direction") == "request")
        assert req_event["server"] == "test-server"
        assert req_event["method"] == "tools/list"
        assert req_event["status"] == "pending"
        assert "payload" in req_event


@pytest.mark.asyncio
async def test_run_wrap_response_has_latency():
    """run_wrap response event includes latency_ms."""
    import os

    with MockIngestServer() as mock:
        api_url = mock.url

        request_msg = {"jsonrpc": "2.0", "method": "initialize", "id": 42, "params": {}}
        request_bytes = json.dumps(request_msg).encode() + b"\n"

        read_fd, write_fd = os.pipe()
        os.write(write_fd, request_bytes)
        os.close(write_fd)

        original_stdin = sys.stdin
        read_file = os.fdopen(read_fd, "rb", buffering=0)
        sys.stdin = type("_FakeStdin", (), {"buffer": read_file})()  # type: ignore

        try:
            await asyncio.wait_for(
                run_wrap("latency-server", [sys.executable, "-c", _ECHO_SCRIPT], api_url=api_url),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("run_wrap timed out")
        finally:
            sys.stdin = original_stdin
            read_file.close()

        await asyncio.sleep(0.1)

        resp_events = [e for e in mock.recorded_events if e.get("direction") == "response"]
        if resp_events:
            resp_event = resp_events[0]
            assert resp_event.get("latency_ms") is not None
            assert resp_event["latency_ms"] >= 0
            assert resp_event["request_id"] is not None


# ---------------------------------------------------------------------------
# POST /ingest endpoint tests
# ---------------------------------------------------------------------------


def test_ingest_endpoint_creates_event():
    """POST /ingest with direction=request creates a new event in the store."""
    from fastapi.testclient import TestClient

    import proxy as proxy_module
    from main import app
    from proxy import clear_events, event_store

    clear_events()
    client = TestClient(app)

    payload = {
        "server": "wrap-server",
        "method": "tools/list",
        "direction": "request",
        "status": "pending",
        "payload": {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    }
    resp = client.post("/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data

    assert len(event_store) == 1
    event = list(event_store)[0]
    assert event.server == "wrap-server"
    assert event.method == "tools/list"
    assert event.direction == "request"
    assert event.status == "pending"

    clear_events()


def test_ingest_endpoint_updates_existing_event():
    """POST /ingest with direction=response and matching request_id updates existing event."""
    from fastapi.testclient import TestClient

    import proxy as proxy_module
    from main import app
    from models import McpEvent
    from proxy import _emit_event, clear_events, event_store

    clear_events()
    client = TestClient(app)

    # Create the original request event
    req_event = McpEvent(
        server="wrap-server",
        method="tools/call",
        direction="request",
        status="pending",
        payload={"jsonrpc": "2.0", "id": 5, "method": "tools/call"},
    )
    _emit_event(req_event, "event_created")

    # Send a response that references the original event's id via request_id
    payload = {
        "server": "wrap-server",
        "method": "tools/call",
        "direction": "response",
        "status": "success",
        "request_id": req_event.id,
        "latency_ms": 42.0,
        "payload": {"jsonrpc": "2.0", "id": 5, "result": {}},
    }
    resp = client.post("/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == req_event.id  # same event updated in-place

    # Only one event should remain (updated, not duplicated)
    assert len(event_store) == 1
    updated = list(event_store)[0]
    assert updated.direction == "response"
    assert updated.status == "success"
    assert updated.latency_ms == 42.0

    clear_events()
