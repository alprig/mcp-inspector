# MCP Inspector

Real-time debugger for MCP (Model Context Protocol) servers. Works like Chrome DevTools Network tab — but for MCP.

Intercepts JSON-RPC traffic between Claude and MCP servers, streams it via WebSocket to a browser dashboard.

```
Claude Code → [Python proxy :4444] → MCP server
                      ↓
               FastAPI WebSocket :8000
                      ↓
               Next.js Dashboard :3333
```

## Features

- **Real-time event log** — every tool call appears instantly via WebSocket push
- **Stats bar** — total requests, avg latency, error rate
- **Filter bar** — filter by server, method, status (AND logic)
- **Server sidebar** — click a server to filter by it
- **Detail panel** — click any row to inspect full JSON payload with syntax highlighting
- **Error view** — errors show message + stack trace prominently

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" mcp websockets pydantic python-dotenv
uvicorn main:app --port 8000
```

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev -- --port 3333
```

Open [http://localhost:3333](http://localhost:3333)

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, WebSocket |
| Transport | stdio subprocess wrapping |

## API

| Endpoint | Description |
|----------|-------------|
| `GET /ws` | WebSocket — streams events, sends last 100 on connect |
| `GET /events?limit=100` | REST — recent events |
| `DELETE /events` | Clear session history |
| `GET /health` | Health check |

## Running tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest
```

## Proxy config

The proxy reads MCP servers from `~/.claude/settings.json` (`mcpServers` block):

```bash
mcp-inspector start   # starts proxy on :4444 + API on :8000
```
