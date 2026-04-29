# MCP Inspector — Status

## Текущий спринт: Sprint 2 — Filters + Stats + Server Config

**Цель:** Фильтрация, статистика сессии, конфигурация серверов

---

## Sprint 1 — Foundation ✅ Done (2026-04-29)

### Epic 1: Core Proxy + Real-time Dashboard

#### Backend (GLM) — PR #7 merged
- [x] US-001: Запуск прокси через CLI (`mcp-inspector start`)
- [x] US-002-BE: WebSocket endpoint для стриминга событий

#### Frontend (MiniMax) — PR #6 merged
- [x] US-002-FE: Real-time лог запросов в дашборде
- [x] US-003: Детальный просмотр запроса/ответа (slide-in panel)

---

## Sprint 2 — Done ✅ (2026-04-29)

### Frontend (MiniMax) — PR #11 merged
- [x] US-004: Фильтрация по серверу / методу / статусу
- [x] US-005: Статистика сессии (кол-во запросов, avg latency, error rate)
- [x] US-006: Конфигурация серверов (sidebar)

---

## Sprint 4 — Done ✅ (2026-04-29)

### Frontend + Backend — PR #26, #27, #28 merged
- [x] US-015: Export session as JSON (кнопка в header)
- [x] US-023: `npx mcp-inspector` one-command setup + README update
- [x] US-025: Replay — кнопка в DetailPanel, `POST /replay/{id}`, `↺` badge

---

## Sprint 3 — Done ✅ (2026-04-29)

### Frontend (MiniMax) — PR #19 merged
- [x] US-007: Текстовый поиск по событиям (tool/server/method/payload, debounce 150ms)
- [x] US-008: Копирование payload в clipboard с визуальным feedback
- [x] US-009: Keyboard navigation (J/K/Enter/Escape//)

### Bug fix #13 — PR #20 + #21 merged
- [x] Backend: паринг request↔response в одно событие (WsMessage typed protocol)
- [x] Frontend: useWebSocket обрабатывает event_created / event_updated / history

---

## Прогресс

| Task | Агент | Статус |
|------|-------|--------|
| US-001 CLI proxy | GLM | ✅ Done |
| US-002 WebSocket BE | GLM | ✅ Done |
| US-002 Real-time FE | MiniMax | ✅ Done |
| US-003 Detail view | MiniMax | ✅ Done |
| US-004 Filters | MiniMax | ✅ Done |
| US-005 Stats | MiniMax | ✅ Done |
| US-006 Server sidebar | MiniMax | ✅ Done |
| US-007 Text search | MiniMax | ✅ Done |
| US-008 Copy payload | MiniMax | ✅ Done |
| US-009 Keyboard nav | MiniMax | ✅ Done |
| Bug #13 Request pairing | GLM + MiniMax | ✅ Done |
| US-015 Export JSON | MiniMax | ✅ Done |
| US-023 npx setup | MiniMax | ✅ Done |
| US-025 Replay | GLM + MiniMax | ✅ Done |

---

## Ссылки

- **GitHub:** https://github.com/alprig/mcp-inspector
- **PRD:** `tasks/01-prd-mcp-inspector.md`
- **Frontend:** localhost:3333 (Next.js)
- **Backend:** localhost:8000 (FastAPI)
- **Proxy:** port 4444

---

## Как запустить

```bash
# Backend (proxy + API)
cd backend && pip install -e . && mcp-inspector start

# Frontend
cd frontend && npm run dev -- --port 3333
```

---

## Агенты

- **GLM** — Python backend (proxy, FastAPI, WebSocket)
- **MiniMax** — Next.js frontend (дашборд, компоненты, UI)
- **Claude (Architect)** — Issues, review, decisions. Код НЕ пишет.
