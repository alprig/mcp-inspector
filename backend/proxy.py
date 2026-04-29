"""stdio proxy logic: subprocess wrapping for MCP servers."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque

from models import McpEvent, McpServerConfig, WsMessage

# Maximum number of events kept in memory
MAX_EVENTS = 1000

# Global in-memory event store
event_store: Deque[McpEvent] = deque(maxlen=MAX_EVENTS)

# Per-websocket asyncio queues — registered by WebSocket handlers
_subscriber_queues: list[asyncio.Queue[WsMessage]] = []

# Mapping from JSON-RPC id → event UUID (for pairing request↔response)
_pending_requests: dict[str | int, str] = {}


def subscribe() -> asyncio.Queue[WsMessage]:
    """Register a new subscriber queue; returns the queue."""
    q: asyncio.Queue[WsMessage] = asyncio.Queue()
    _subscriber_queues.append(q)
    return q


def unsubscribe(q: asyncio.Queue[WsMessage]) -> None:
    """Remove a subscriber queue."""
    try:
        _subscriber_queues.remove(q)
    except ValueError:
        pass


def clear_events() -> None:
    """Clear all stored events and pending request mappings."""
    event_store.clear()
    _pending_requests.clear()


def _broadcast(event: McpEvent, msg_type: str) -> None:
    """Push a WsMessage into all subscriber queues."""
    ws_msg = WsMessage(type=msg_type, event=event)  # type: ignore[arg-type]
    for q in list(_subscriber_queues):
        try:
            q.put_nowait(ws_msg)
        except asyncio.QueueFull:
            pass


def _emit_event(event: McpEvent, msg_type: str = "event_created") -> None:
    """Store event and push it into all subscriber queues."""
    event_store.append(event)
    _broadcast(event, msg_type)


def _log_event(event: McpEvent) -> None:
    """Write JSON log line to stdout."""
    log_line = {
        "timestamp": event.timestamp.isoformat(),
        "server": event.server,
        "method": event.method,
        "direction": event.direction,
        "status": event.status,
        "payload": event.payload,
    }
    print(json.dumps(log_line), flush=True)


class McpProxy:
    """Wraps a single MCP server subprocess and intercepts stdio."""

    def __init__(self, server_name: str, config: McpServerConfig) -> None:
        self.server_name = server_name
        self.config = config
        self._process: asyncio.subprocess.Process | None = None
        # Track pending requests: JSON-RPC id → (method, start_time)
        self._pending: dict[str | int, tuple[str, float]] = {}

    async def start(self) -> None:
        """Launch the MCP server subprocess."""
        env = dict(os.environ)
        if self.config.env:
            env.update(self.config.env)

        cmd = [self.config.command] + self.config.args
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

    async def stop(self) -> None:
        """Terminate the subprocess."""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def send_request(self, data: bytes) -> None:
        """Forward a raw JSON-RPC request to the subprocess stdin."""
        if self._process and self._process.stdin:
            self._process.stdin.write(data + b"\n")
            await self._process.stdin.drain()

            # Parse and log the request
            try:
                msg = json.loads(data)
                method = msg.get("method", "unknown")
                req_id = msg.get("id")
                now = time.monotonic()
                if req_id is not None:
                    self._pending[req_id] = (method, now)

                tool: str | None = None
                if method == "tools/call":
                    tool = (msg.get("params") or {}).get("name")

                # Convert req_id to str for storage in request_id field
                request_id_str: str | None = str(req_id) if req_id is not None else None

                event = McpEvent(
                    timestamp=datetime.now(timezone.utc),
                    server=self.server_name,
                    tool=tool,
                    method=method,
                    direction="request",
                    status="pending",
                    request_id=request_id_str,
                    payload=msg,
                )
                _emit_event(event, "event_created")
                # Record mapping: JSON-RPC id → event UUID for response pairing
                if req_id is not None:
                    _pending_requests[req_id] = event.id
                _log_event(event)
            except json.JSONDecodeError:
                pass

    async def read_response(self) -> bytes | None:
        """Read one line from the subprocess stdout."""
        if self._process and self._process.stdout:
            line = await self._process.stdout.readline()
            if line:
                self._handle_response(line.rstrip(b"\n"))
            return line if line else None
        return None

    def _handle_response(self, data: bytes) -> None:
        """Parse and log a JSON-RPC response, pairing with the original request event."""
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            return

        req_id = msg.get("id")
        method = "unknown"
        latency: float | None = None

        if req_id is not None and req_id in self._pending:
            method, start = self._pending.pop(req_id)
            latency = (time.monotonic() - start) * 1000

        status: str = "success"
        if "error" in msg:
            status = "error"

        # Try to find and update the existing request event
        if req_id is not None and req_id in _pending_requests:
            event_id = _pending_requests.pop(req_id)
            existing = next((e for e in event_store if e.id == event_id), None)
            if existing is not None:
                existing.status = status  # type: ignore[assignment]
                existing.latency_ms = latency
                existing.payload = msg
                existing.direction = "response"
                _broadcast(existing, "event_updated")
                _log_event(existing)
                return

        # Fallback: no matching request found — create a new event
        event = McpEvent(
            timestamp=datetime.now(timezone.utc),
            server=self.server_name,
            tool=None,
            method=method,
            direction="response",
            status=status,  # type: ignore[arg-type]
            latency_ms=latency,
            payload=msg,
        )
        _emit_event(event, "event_created")
        _log_event(event)


class ProxyManager:
    """Manages multiple MCP server proxies."""

    def __init__(self) -> None:
        self._proxies: dict[str, McpProxy] = {}

    def add_proxy(self, name: str, config: McpServerConfig) -> McpProxy:
        proxy = McpProxy(name, config)
        self._proxies[name] = proxy
        return proxy

    def get_proxy(self, name: str) -> McpProxy | None:
        return self._proxies.get(name)

    @property
    def proxies(self) -> dict[str, McpProxy]:
        return dict(self._proxies)

    async def start_all(self) -> None:
        for proxy in self._proxies.values():
            await proxy.start()

    async def stop_all(self) -> None:
        for proxy in self._proxies.values():
            await proxy.stop()
