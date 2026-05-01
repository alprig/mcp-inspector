"""stdio wrapper: intercepts MCP stdio traffic, posts events to inspector backend."""

from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from datetime import datetime, timezone

_DEFAULT_API = "http://localhost:8000"


async def _post_ingest(url: str, payload: dict) -> None:
    """Fire-and-forget HTTP POST. Swallows all errors."""
    import urllib.error
    import urllib.request

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=0.5)
    except Exception:
        pass


def _bg(coro) -> None:
    """Schedule coroutine as background task."""
    asyncio.create_task(coro)


def _derive_name(cmd: list[str]) -> str:
    """Derive server name from command list.

    Examples::
        ["npx", "@modelcontextprotocol/server-filesystem", "/path"] -> "server-filesystem"
        ["python", "my_server.py"] -> "my_server"
        ["node", "server.js"] -> "server"
    """
    _skip_cmds = {"npx", "node", "python", "python3", "uvx"}

    # Prefer npm package names (contain @ or look like package paths without leading /)
    # and script file names over plain directory arguments.
    # Iterate forward so we pick the first meaningful non-launcher argument.
    for part in cmd:
        if part in _skip_cmds:
            continue
        if part.startswith("-"):
            continue
        # Skip bare filesystem paths that are pure directories (no extension, no @, starts /)
        # These are typically positional args to the server, not the server name.
        if part.startswith("/") and "@" not in part and "." not in part.rsplit("/", 1)[-1]:
            continue
        # The basename after the last / or \, then strip extension
        name = part.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        name = name.rsplit(".", 1)[0]  # strip extension (.py, .js, etc.)
        if name and name not in _skip_cmds:
            return name
    return cmd[0] if cmd else "unknown"


async def run_wrap(
    server_name: str, cmd: list[str], api_url: str = _DEFAULT_API
) -> None:
    """Main wrapper coroutine: intercept stdio between Claude Code and real MCP server."""
    ingest_url = f"{api_url}/ingest"

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # pending[json_rpc_id] = (method, start_monotonic, req_event_id)
    pending: dict[str | int, tuple[str, float, str]] = {}

    # Connect sys.stdin asynchronously
    loop = asyncio.get_running_loop()
    stdin_reader = asyncio.StreamReader()
    stdin_proto = asyncio.StreamReaderProtocol(stdin_reader)
    await loop.connect_read_pipe(lambda: stdin_proto, sys.stdin.buffer)

    async def handle_stdin() -> None:
        while True:
            line = await stdin_reader.readline()
            if not line:
                break
            assert proc.stdin is not None
            proc.stdin.write(line)
            await proc.stdin.drain()

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = msg.get("method", "unknown")
            req_id = msg.get("id")
            req_event_id = str(uuid.uuid4())

            if req_id is not None:
                pending[req_id] = (method, time.monotonic(), req_event_id)

            tool: str | None = None
            if method == "tools/call":
                tool = (msg.get("params") or {}).get("name")

            event = {
                "id": req_event_id,
                "server": server_name,
                "method": method,
                "tool": tool,
                "direction": "request",
                "status": "pending",
                "request_id": None,
                "latency_ms": None,
                "payload": msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "replayed": False,
            }
            _bg(_post_ingest(ingest_url, event))

    async def handle_stdout() -> None:
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            req_id = msg.get("id")
            method = "unknown"
            latency_ms: float | None = None
            request_id: str | None = None

            if req_id is not None and req_id in pending:
                method, start, req_event_id = pending.pop(req_id)
                latency_ms = (time.monotonic() - start) * 1000
                request_id = req_event_id

            status = "error" if "error" in msg else "success"

            event = {
                "server": server_name,
                "method": method,
                "tool": None,
                "direction": "response",
                "status": status,
                "request_id": request_id,
                "latency_ms": latency_ms,
                "payload": msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "replayed": False,
            }
            _bg(_post_ingest(ingest_url, event))

    async def handle_stderr() -> None:
        assert proc.stderr is not None
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            sys.stderr.buffer.write(line)
            sys.stderr.buffer.flush()

    try:
        await asyncio.gather(handle_stdin(), handle_stdout(), handle_stderr())
    finally:
        if proc.returncode is None:
            proc.terminate()
        await proc.wait()
