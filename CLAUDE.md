# MCP Inspector — Project Context

## Что это
MCP Inspector — инструмент отладки MCP серверов. Прокси между Claude и MCP серверами + браузерный дашборд. Показывает все JSON-RPC запросы/ответы в реальном времени. Как Chrome DevTools Network, но для MCP.

## Репозиторий
https://github.com/alprig/mcp-inspector

## Стек
- **Frontend:** Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui → `/frontend`
- **Backend:** Python FastAPI + WebSocket + MCP SDK → `/backend`
- **LSP:** TypeScript LSP (frontend) + pylsp (backend) + ast-index

## Архитектура
```
Claude Code → [Python proxy] → реальный MCP сервер
                   ↓
            FastAPI WebSocket
                   ↓
          Next.js Dashboard :3333
```

## Роли агентов
- **Я (Claude)** — архитектор: создаю Issues, ревьюю, принимаю решения. Код НЕ пишу.
- **GLM** — пишет Python backend (proxy, FastAPI, WebSocket)
- **MiniMax** — пишет Next.js frontend (дашборд, компоненты, UI)

## Workflow
1. Я создаю GitHub Issue (Task)
2. Агент берёт задачу, пишет код в worktree ветке
3. Открывает PR, линкует к Issue
4. Я ревьюю → галочка в Issue → merge → следующий Task

## GitHub Issues структура
- **Epic** = большая фича (родительский Issue с label `epic`)
- **Task** = конкретная задача (дочерний Issue с label `task`, linked к Epic)
- Acceptance Criteria в каждом Task = чекбоксы `- [ ]`
- Статусы через GitHub Projects: Backlog → In Progress → Review → Done

## Команды
```bash
# Frontend
cd frontend && npm run dev        # localhost:3000
cd frontend && npm run typecheck  # TypeScript check
cd frontend && npm run lint       # ESLint

# Backend
cd backend && uvicorn main:app --reload --port 8000
cd backend && pytest
```

## LSP правила
- ВСЕГДА использовать LSP перед изменением файла
- `documentSymbol` для понимания структуры
- `hover` для проверки типов
- ast-index rebuild после добавления новых файлов
- Запускать typecheck после каждого изменения TypeScript файла

## PRD
Полный PRD: `tasks/01-prd-mcp-inspector.md`

## Skills
- `/prd` — генерация PRD
- `/init-dev` — scaffold dev skill (запустить после первого спринта кода)
- `/dev <issue>` — разработка GitHub Issue end-to-end (после init-dev)

## Текущий статус
См. `STATUS.md`

---

## Как работает сессия

**Я — оркестратор.** Я сам спавню агентов через Agent tool, они пишут код автономно в изолированных ветках, открывают PR. Ты только говоришь мне что делать — дальше я сам.

### Команды

- `спринт` — запустить текущий спринт: я читаю Issues, спавню backend и frontend агентов параллельно, они пишут код в отдельных ветках, открывают PR
- `ревью` — я ревьюю открытые PR, ставлю галочки в Issues, говорю merge или что исправить
- `статус` — я показываю что сделано, что в работе, что заблокировано

### Как я работаю

1. Читаю STATUS.md + GitHub Issues
2. Спавню **backend агента** (GLM роль) — пишет Python в ветке `feature/backend-*`
3. Спавню **frontend агента** (MiniMax роль) — пишет Next.js в ветке `feature/frontend-*`
4. Агенты работают параллельно в изолированных worktree
5. Когда агент готов — он делает commit + push + открывает PR с `Closes #N`
6. Я ревьюю PR → ставлю галочки в GitHub Issue → говорю тебе merge

### Правила агентов

Каждый агент которого я спавню:
- Работает только в своей зоне (backend/ или frontend/)
- Проверяет типы после каждого изменения (`pytest` / `npm run typecheck`)
- Использует LSP перед изменением файлов
- Открывает PR с `Closes #N` в описании
- Не трогает чужие файлы
