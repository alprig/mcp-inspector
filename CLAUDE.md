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

**Ты — relay между мной и агентами.** Я говорю что и кому дать, ты копируешь и вставляешь.

### Старт

Напиши `спринт` — я прочитаю STATUS.md + GitHub Issues и сразу выдам первый промт с пометкой кому он.

### Формат моих команд

Я всегда буду писать так:

```
→ GLM:
[промт]
```
или
```
→ MiniMax:
[промт]
```

Ты копируешь блок и вставляешь в соответствующее окно. Агент отвечает — ты вставляешь ответ сюда. Я смотрю, решаю что дальше, выдаю следующий промт.

### Цикл работы

1. Я выдаю промт → `→ GLM` или `→ MiniMax`
2. Ты даёшь агенту, он пишет код / отвечает
3. Ты вставляешь ответ агента сюда
4. Я ревьюю → выдаю следующий промт или говорю что исправить
5. Когда таск готов — я ставлю галочки в GitHub Issue и говорю `merge`

### Команды

- `спринт` — начать спринт, я выдам первые промты
- `вот ответ GLM: [текст]` — показать мне ответ GLM
- `вот ответ MiniMax: [текст]` — показать мне ответ MiniMax
- `вот PR: [ссылка]` — я ревьюю PR
- `статус` — я покажу что сделано, что в работе
