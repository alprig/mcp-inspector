[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-%3E%3D18-green)](https://nodejs.org/)

# MCP Inspector

Real-time debugger for MCP servers. Like Chrome DevTools Network — but for MCP.

## Quick Start

```bash
# 1. Start the inspector
npx github:alprig/mcp-inspector

# 2. Wrap your MCP servers (in a new terminal)
npx github:alprig/mcp-inspector setup

# 3. Restart Claude Code — traffic appears in the dashboard
```

Open [http://localhost:3333](http://localhost:3333)

## How it works

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

## Supported transports

`stdio ✓` | `HTTP/SSE — coming soon`

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
