"""FastAPI app: WebSocket endpoint + REST API for MCP event streaming.

US-001: CLI proxy startup
US-002-BE: WebSocket streaming
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from typing import Literal as _Literal

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

import proxy as proxy_module
from config import load_config
from models import McpEvent, WsMessage


app = FastAPI(title="MCP Inspector", version="0.1.0")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint: sends history on connect, then streams live events."""
    await websocket.accept()

    # Send last 100 historical events immediately as typed messages
    history = list(proxy_module.event_store)[-100:]
    for event in history:
        try:
            msg = WsMessage(type="history", event=event)
            await websocket.send_text(msg.model_dump_json())
        except Exception:
            return

    # Subscribe to new events
    queue = proxy_module.subscribe()

    # Run two tasks concurrently:
    # 1. Listen for incoming messages (ping/close)
    # 2. Stream new events from queue to client
    async def send_events() -> None:
        while True:
            ws_msg: WsMessage = await queue.get()
            try:
                await websocket.send_text(ws_msg.model_dump_json())
            except Exception:
                break

    async def receive_messages() -> None:
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception:
                break

    try:
        send_task = asyncio.create_task(send_events())
        recv_task = asyncio.create_task(receive_messages())
        # Wait for either task to finish (disconnect or error)
        done, pending = await asyncio.wait(
            [send_task, recv_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        proxy_module.unsubscribe(queue)


@app.get("/events")
async def get_events(limit: int = 100) -> list[dict]:
    """Return recent events (up to limit, default 100)."""
    events = list(proxy_module.event_store)
    return [e.model_dump(mode="json") for e in events[-limit:]]


@app.delete("/events")
async def delete_events() -> dict:
    """Clear all stored events."""
    proxy_module.clear_events()
    return {"status": "cleared"}


@app.post("/replay/{event_id}")
async def replay_event(event_id: str) -> dict:
    """Replay a previously captured request event through the same proxy."""
    # 1. Find the event in the store
    event = next((e for e in proxy_module.event_store if e.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # 2. Only request events can be replayed
    if event.direction != "request":
        raise HTTPException(status_code=400, detail="Can only replay request events")

    # 3. Look up the proxy for this server
    proxy = proxy_module.manager.get_proxy(event.server)
    if not proxy or not proxy.is_running:
        raise HTTPException(
            status_code=503,
            detail=f"Proxy for server '{event.server}' is not running",
        )

    # 4. Send the payload as a JSON-RPC request
    import json as _json

    await proxy.send_request(_json.dumps(event.payload).encode())

    # 5. The new replay event is created inside send_request; return the latest event id
    new_event_id = list(proxy_module.event_store)[-1].id
    return {"ok": True, "event_id": new_event_id}


# ---------------------------------------------------------------------------
# POST /ingest  (US-029: wrap command)
# ---------------------------------------------------------------------------


class IngestPayload(BaseModel):
    id: str | None = None
    request_id: str | None = None
    server: str
    method: str
    tool: str | None = None
    direction: _Literal["request", "response"]
    status: _Literal["success", "error", "pending"]
    latency_ms: float | None = None
    payload: dict
    timestamp: datetime | None = None
    replayed: bool = False


@app.post("/ingest")
async def ingest_event(body: IngestPayload) -> dict:
    """Receive an event from a wrap process, store and broadcast it."""
    from datetime import datetime, timezone as _tz
    import uuid as _uuid

    if body.direction == "response" and body.request_id:
        # Try to update existing request event
        existing = next(
            (e for e in proxy_module.event_store if e.id == body.request_id),
            None,
        )
        if existing is not None:
            existing.status = body.status  # type: ignore[assignment]
            existing.latency_ms = body.latency_ms
            existing.payload = body.payload
            existing.direction = "response"
            proxy_module._broadcast(existing, "event_updated")
            return {"id": existing.id}

    # Create new event
    event = McpEvent(
        id=body.id or str(_uuid.uuid4()),
        server=body.server,
        method=body.method,
        tool=body.tool,
        direction=body.direction,
        status=body.status,
        latency_ms=body.latency_ms,
        request_id=body.request_id,
        payload=body.payload,
        timestamp=body.timestamp or datetime.now(_tz.utc),
        replayed=body.replayed,
    )
    proxy_module._emit_event(event, "event_created")
    return {"id": event.id}


# ---------------------------------------------------------------------------
# CLI entry point  (US-001)
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI: `mcp-inspector start` — launches proxy and API server."""
    import argparse

    from wrap import _derive_name, run_wrap

    parser = argparse.ArgumentParser(description="MCP Inspector proxy")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start", help="Start the MCP Inspector proxy")

    wrap_parser = sub.add_parser("wrap", help="Wrap an MCP server for inspection")
    wrap_parser.add_argument(
        "--name", default=None, help="Server name (default: derived from command)"
    )
    wrap_parser.add_argument(
        "--api", default="http://localhost:8000", help="Inspector API URL"
    )
    wrap_parser.add_argument("cmd", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.command == "start":
        _start()
    elif args.command == "wrap":
        cmd = args.cmd
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print("Error: no command specified after wrap", file=sys.stderr)
            sys.exit(1)
        name = args.name or _derive_name(cmd)
        asyncio.run(run_wrap(name, cmd, api_url=args.api))
    else:
        parser.print_help()
        sys.exit(1)


async def _run() -> None:
    """Async entry point: start all MCP proxies, then serve the FastAPI app."""
    cfg = load_config()
    for name, srv_cfg in cfg.mcp_servers.items():
        proxy_module.manager.add_proxy(name, srv_cfg)

    print(f"Loaded {len(cfg.mcp_servers)} MCP server(s)")
    print("Inspector running at http://localhost:3333")
    print("API running at http://localhost:8000")

    # TODO: add TCP listener on port 4444 to forward connections to proxies

    await proxy_module.manager.start_all()

    uvicorn_config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(uvicorn_config)

    try:
        await server.serve()
    finally:
        await proxy_module.manager.stop_all()


def _start() -> None:
    """Start the proxy subprocesses and API server on port 8000."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
