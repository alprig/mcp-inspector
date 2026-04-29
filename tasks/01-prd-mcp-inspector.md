# PRD: MCP Inspector

## Introduction

MCP Inspector — инструмент отладки MCP серверов для разработчиков использующих Claude Code. Это прокси который перехватывает весь трафик между Claude и MCP серверами, показывает каждый JSON-RPC запрос и ответ в реальном времени в браузерном дашборде. Аналог Chrome DevTools Network tab, но для MCP.

**Проблема:** Когда MCP сервер не работает — непонятно где сломалось. В Claude? В сервере? В конфиге? Сейчас это чёрный ящик без инструментов диагностики.

**Решение:** CLI прокси + веб-дашборд. Open source, бесплатно. Hosted версия за $9/мес.

## Goals

- Показывать все tool_call запросы и ответы между Claude и MCP серверами в реальном времени
- Отображать задержку каждого вызова, статус, payload
- Помочь разработчику быстро найти где именно сломалось
- Работать как drop-in замена без изменения конфига Claude Code
- Открытый исходный код → вирусное распространение через GitHub/HN

## User Stories

### US-001: Запуск прокси через CLI
**Description:** As a developer, I want to start MCP Inspector with one command so that all MCP traffic goes through it automatically.

**Acceptance Criteria:**
- [ ] `mcp-inspector start` запускает прокси на порту 4444
- [ ] Прокси автоматически определяет все MCP серверы из `~/.claude/settings.json`
- [ ] Выводит в терминал URL дашборда: `Inspector running at http://localhost:3333`
- [ ] Прокси прозрачно форвардит все запросы без изменений
- [ ] Typecheck passes

### US-002: Real-time лог запросов в дашборде
**Description:** As a developer, I want to see all MCP tool calls in real-time so that I can understand what Claude is doing.

**Acceptance Criteria:**
- [ ] Каждый tool_call отображается в списке немедленно (WebSocket push)
- [ ] Показывается: время, имя сервера, имя инструмента, статус (success/error), задержка ms
- [ ] Новые запросы добавляются сверху без перезагрузки страницы
- [ ] Цветовая индикация: зелёный = success, красный = error, жёлтый = timeout
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-003: Детальный просмотр запроса/ответа
**Description:** As a developer, I want to inspect the full payload of any MCP call so that I can debug data issues.

**Acceptance Criteria:**
- [ ] Клик на запрос открывает детальную панель
- [ ] Показывает полный JSON запроса (tool input params)
- [ ] Показывает полный JSON ответа (tool result)
- [ ] JSON подсвечен синтаксисом, collapse/expand для вложенных объектов
- [ ] Показывает стек ошибки если error
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-004: Фильтрация по серверу и инструменту
**Description:** As a developer, I want to filter calls by server or tool name so that I can focus on specific issues.

**Acceptance Criteria:**
- [ ] Фильтр по имени MCP сервера (dropdown)
- [ ] Фильтр по имени инструмента (input search)
- [ ] Фильтр по статусу: All / Success / Error
- [ ] Фильтры комбинируются (AND логика)
- [ ] Сброс всех фильтров одной кнопкой
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-005: Статистика сессии
**Description:** As a developer, I want to see session statistics so that I can understand overall performance.

**Acceptance Criteria:**
- [ ] Header показывает: всего вызовов, ошибок, avg latency
- [ ] Обновляется в реальном времени
- [ ] Кнопка "Clear" очищает всю историю сессии
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-006: Конфигурация серверов
**Description:** As a developer, I want to see which MCP servers are connected so that I know the proxy is working correctly.

**Acceptance Criteria:**
- [ ] Sidebar показывает список всех MCP серверов из config
- [ ] Статус каждого: connected / disconnected / error
- [ ] Показывает список доступных инструментов каждого сервера
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: Python прокси перехватывает stdio транспорт MCP серверов через subprocess wrapping
- FR-2: Прокси логирует каждый JSON-RPC запрос и ответ с timestamp и duration
- FR-3: FastAPI WebSocket endpoint стримит события на фронтенд в реальном времени
- FR-4: Next.js дашборд отображает лог на `http://localhost:3333`
- FR-5: Прокси читает конфиг из `~/.claude/settings.json` автоматически
- FR-6: Фильтрация и поиск на фронтенде (client-side, no server round-trip)
- FR-7: JSON viewer с syntax highlighting и collapse/expand
- FR-8: Статистика: total calls, error rate, avg/p95 latency

## Non-Goals

- Не редактирует или модифицирует MCP запросы (только читает)
- Не сохраняет историю между сессиями (только in-memory)
- Не поддерживает HTTP/SSE transport в MVP (только stdio)
- Не имеет аутентификации в MVP
- Не работает с несколькими Claude сессиями одновременно
- Нет мобильной версии

## Technical Considerations

**Стек:**
- Frontend: Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Python FastAPI + WebSocket + MCP SDK
- Transport: stdio proxy через subprocess
- IPC: WebSocket между backend и frontend

**Архитектура прокси:**
```
Claude Code → [mcp-inspector proxy] → реальный MCP сервер
                      ↓
               FastAPI WebSocket
                      ↓
               Next.js Dashboard
```

**Агенты:**
- GLM пишет: Python backend (proxy, FastAPI, WebSocket, MCP перехват)
- MiniMax пишет: Next.js frontend (дашборд, компоненты, real-time UI)

**LSP:**
- TypeScript LSP для frontend (типы, компоненты)
- Python LSP (pylsp) для backend (типы, FastAPI роуты)
- ast-index для сканирования конвенций

## Success Metrics

- `mcp-inspector start` → дашборд открывается за < 3 секунды
- Задержка отображения события: < 100ms от момента вызова
- 100+ GitHub stars за первую неделю после запуска на HN/Reddit
- Первые 10 платящих пользователей hosted версии за 30 дней

## Open Questions

- Нужен ли replay функционал (повторить запрос)? → v1.1
- Экспорт логов в JSON/HAR формат? → v1.1
- Поддержка HTTP/SSE transport? → v1.1
