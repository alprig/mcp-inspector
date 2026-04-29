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

## Как начать новую сессию

**Команда:** напиши `спринт` — и я сделаю всё сам:

1. Прочитаю `STATUS.md` и открытые GitHub Issues
2. Определю что делает GLM, что делает MiniMax
3. Сгенерирую готовые промты для каждого агента
4. Ты копируешь промт → вставляешь в окно с нужным агентом
5. Агент пишет код, открывает PR
6. Ты скидываешь мне PR → я ревьюю → ставлю галочку в Issue → merge

**Команда для ревью:** напиши `ревью PR #N` — я проверю PR и дам фидбек.

**Команда для галочки:** напиши `закрыть #N` — я отмечу acceptance criteria и закрою Issue.

### Правила для агентов (вшить в промт)

Каждый промт для GLM/MiniMax должен содержать:
- Ссылку на GitHub Issue с полным описанием
- Файловую структуру которую нужно создать
- Команду для проверки (`pytest` / `npm run typecheck`)
- Требование открыть PR и залинковать к Issue (`Closes #N`)
- Запрет менять файлы вне своей зоны ответственности
