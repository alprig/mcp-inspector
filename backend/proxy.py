"""stdio proxy logic: subprocess wrapping for MCP servers."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque

from models import McpEvent, McpServerConfig

# Maximum number of events kept in memory
MAX_EVENTS = 1000

# Global in-memory event store
event_store: Deque[McpEvent] = deque(maxlen=MAX_EVENTS)

# Per-websocket asyncio queues — registered by WebSocket handlers
_subscriber_queues: list[asyncio.Queue[McpEvent]] = []


def subscribe() -> asyncio.Queue[McpEvent]:
    """Register a new subscriber queue; returns the queue."""
    q: asyncio.Queue[McpEvent] = asyncio.Queue()
    _subscriber_queues.append(q)
    return q


def unsubscribe(q: asyncio.Queue[McpEvent]) -> None:
    """Remove a subscriber queue."""
    try:
        _subscriber_queues.remove(q)
    except ValueError:
        pass


def clear_events() -> None:
    """Clear all stored events."""
    event_store.clear()


def _emit_event(event: McpEvent) -> None:
    """Store event and push it into all subscriber queues."""
    event_store.append(event)
    for q in list(_subscriber_queues):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


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
        # Track pending requests: id → (method, start_time)
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

                event = McpEvent(
                    timestamp=datetime.now(timezone.utc),
                    server=self.server_name,
                    tool=tool,
                    method=method,
                    direction="request",
                    status="pending",
                    payload=msg,
                )
                _emit_event(event)
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
        """Parse and log a JSON-RPC response."""
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
        _emit_event(event)
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
