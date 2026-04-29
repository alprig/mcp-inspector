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

## Sprint 3 — Backlog

*Нет запланированных задач. Добавь следующий спринт.*

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
