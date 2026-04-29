# MCP Inspector — Status

## Текущий спринт: Sprint 1 — Foundation

**Цель:** Базовая архитектура работает end-to-end (прокси + WebSocket + дашборд)

**Дата старта:** 2026-04-28

---

## Epic 1: Core Proxy + Real-time Dashboard

### Backend (GLM)
- [ ] US-001: Запуск прокси через CLI
- [ ] US-002-BE: WebSocket endpoint для стриминга событий

### Frontend (MiniMax)
- [ ] US-002-FE: Real-time лог запросов в дашборде
- [ ] US-003: Детальный просмотр запроса/ответа

### Next sprint
- US-004: Фильтрация
- US-005: Статистика сессии
- US-006: Конфигурация серверов (sidebar)

---

## Прогресс

| Task | Агент | Статус |
|------|-------|--------|
| US-001 CLI proxy | GLM | Backlog |
| US-002 WebSocket BE | GLM | Backlog |
| US-002 Real-time FE | MiniMax | Backlog |
| US-003 Detail view | MiniMax | Backlog |
| US-004 Filters | MiniMax | Backlog |
| US-005 Stats | MiniMax | Backlog |
| US-006 Server sidebar | MiniMax | Backlog |

---

## Ссылки

- **GitHub:** https://github.com/alprig/mcp-inspector
- **PRD:** `tasks/01-prd-mcp-inspector.md`
- **Frontend:** localhost:3333 (Next.js)
- **Backend:** localhost:8000 (FastAPI)
- **Proxy:** port 4444

---

## Что запущено

```bash
# Запустить backend
cd backend && uvicorn main:app --reload --port 8000

# Запустить frontend  
cd frontend && npm run dev -- --port 3333
```

---

## Агенты

- **GLM** — Python backend (proxy, FastAPI, WebSocket)
- **MiniMax** — Next.js frontend (дашборд, компоненты, UI)
- **Claude (Architect)** — Issues, review, decisions. Код НЕ пишет.
