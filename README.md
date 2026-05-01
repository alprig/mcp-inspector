[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-%3E%3D18-green)](https://nodejs.org/)

# MCP Inspector

Real-time debugger for MCP (Model Context Protocol) servers. Works like Chrome DevTools Network tab — but for MCP.

Intercepts JSON-RPC traffic between Claude and MCP servers, streams it via WebSocket to a browser dashboard.

```
Claude Code → [wrap process] → MCP server
                    ↓
         POST http://localhost:8000/ingest
                    ↓
         FastAPI WebSocket :8000
                    ↓
         Next.js Dashboard :3333
```

## Features

- **Real-time event log** — every tool call appears instantly via WebSocket push
- **Stats bar** — total requests, avg latency, error rate
- **Filter bar** — filter by server, method, status (AND logic)
- **Full-text search** — search across tool names, servers, and JSON payloads
- **Server sidebar** — click a server to filter by it
- **Detail panel** — click any row to inspect full JSON payload with syntax highlighting
- **Error view** — errors show message + stack trace prominently
- **Export JSON** — download the current session as a JSON file

## Quick Start

```bash
npx github:alprig/mcp-inspector
```

Opens the dashboard at [http://localhost:3333](http://localhost:3333). Requires Python 3.11+ and Node 18+.

Dependencies (frontend + backend) are installed automatically on first run.

## Manual setup

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

## Connecting to Claude Code

**Step 1** — start the inspector (keep it running):

```bash
npx github:alprig/mcp-inspector
```

**Step 2** — wrap your MCP servers in `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "github:alprig/mcp-inspector", "wrap", "--",
        "npx", "@modelcontextprotocol/server-filesystem", "/Users/you/projects"
      ]
    }
  }
}
```

The `wrap` command sits between Claude Code and the real MCP server, logging all JSON-RPC traffic to the dashboard. Use `--name <label>` to override the server name shown in the UI.

**Step 3** — open [http://localhost:3333](http://localhost:3333) and run any Claude Code prompt that uses tools. Requests appear in real-time.

> The inspector must be running on `:8000` before Claude Code starts. If the backend is unreachable, `wrap` passes stdio through silently — tool calls still work, they just won't appear in the dashboard.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /ws` | WebSocket — streams events, sends last 100 on connect |
| `GET /events?limit=100` | REST — recent events |
| `DELETE /events` | Clear session history |
| `GET /health` | Health check |
| `POST /ingest` | Receive event from a wrap process |

## Running tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest
```
