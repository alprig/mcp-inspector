"""FastAPI app: WebSocket endpoint + REST API for MCP event streaming.

US-001: CLI proxy startup
US-002-BE: WebSocket streaming
"""

from __future__ import annotations

import asyncio
import sys

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

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


# ---------------------------------------------------------------------------
# CLI entry point  (US-001)
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI: `mcp-inspector start` — launches proxy and API server."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Inspector proxy")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start", help="Start the MCP Inspector proxy")
    args = parser.parse_args()

    if args.command == "start":
        _start()
    else:
        parser.print_help()
        sys.exit(1)


async def _run() -> None:
    """Async entry point: start all MCP proxies, then serve the FastAPI app."""
    cfg = load_config()
    manager = proxy_module.ProxyManager()
    for name, srv_cfg in cfg.mcp_servers.items():
        manager.add_proxy(name, srv_cfg)

    print(f"Loaded {len(cfg.mcp_servers)} MCP server(s)")
    print("Inspector running at http://localhost:3333")
    print("API running at http://localhost:8000")

    # TODO: add TCP listener on port 4444 to forward connections to proxies

    await manager.start_all()

    uvicorn_config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(uvicorn_config)

    try:
        await server.serve()
    finally:
        await manager.stop_all()


def _start() -> None:
    """Start the proxy subprocesses and API server on port 8000."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
