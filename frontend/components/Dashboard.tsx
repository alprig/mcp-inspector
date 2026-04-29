"use client";

import { useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useKeyboardNav } from "@/hooks/useKeyboardNav";
import { ConnectionStatus } from "./ConnectionStatus";
import { EventList } from "./EventList";
import { DetailPanel } from "./DetailPanel";
import { StatsBar } from "./StatsBar";
import { FilterBar } from "./FilterBar";
import { Sidebar } from "./Sidebar";
import type { McpEvent } from "@/types/events";

interface Filters {
  server: string | null;
  method: string | null;
  status: McpEvent["status"] | null;
  searchQuery: string;
}

export function Dashboard() {
  const { events, status, clearEvents } = useWebSocket();
  const [selectedEvent, setSelectedEvent] = useState<McpEvent | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  // Filters state (US-007: includes committed search query)
  const [filters, setFilters] = useState<Filters>({
    server: null,
    method: null,
    status: null,
    searchQuery: "",
  });

  // Separate display value for search input to allow debouncing (US-007)
  const [searchDisplay, setSearchDisplay] = useState("");

  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Search input ref for "/" keyboard shortcut (US-009)
  const searchInputRef = useRef<HTMLInputElement>(null);

  const handleSelectEvent = (event: McpEvent) => {
    setSelectedEvent((prev) => (prev?.id === event.id ? null : event));
  };

  const handleOpenPanel = (event: McpEvent) => {
    setSelectedEvent(event);
    setPanelOpen(true);
  };

  const handleClosePanel = () => {
    setPanelOpen(false);
  };

  const handleFilterChange = (newFilters: Filters) => {
    setFilters(newFilters);
    // When "Clear filters" resets searchQuery, also reset display
    if (newFilters.searchQuery === "") {
      setSearchDisplay("");
    }
  };

  // Computed filtered events — applies all filters AND search (US-007)
  const filteredEvents = events.filter((e) => {
    if (filters.server && e.server !== filters.server) return false;
    if (filters.method && e.method !== filters.method) return false;
    if (filters.status && e.status !== filters.status) return false;
    if (filters.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      const matchesField =
        (e.tool ?? "").toLowerCase().includes(q) ||
        e.server.toLowerCase().includes(q) ||
        e.method.toLowerCase().includes(q);
      const matchesPayload = JSON.stringify(e.payload).toLowerCase().includes(q);
      if (!matchesField && !matchesPayload) return false;
    }
    return true;
  });

  const handleSelectServer = (server: string | null) => {
    setFilters((prev) => ({ ...prev, server }));
  };

  // US-015: Export session as JSON
  const handleExport = () => {
    const data = {
      exported_at: new Date().toISOString(),
      events:
        filteredEvents.length < events.length ? filteredEvents : events,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mcp-session-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // US-009: keyboard navigation
  useKeyboardNav({
    events: filteredEvents,
    selectedId: selectedEvent?.id ?? null,
    onSelect: (event) => {
      setSelectedEvent(event);
    },
    onOpen: handleOpenPanel,
    onClose: () => {
      if (panelOpen) setPanelOpen(false);
    },
    searchInputRef,
  });

  return (
    <div className="h-screen flex flex-col bg-gray-950 overflow-hidden">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm shrink-0 z-30">
        <div className="px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <svg
                className="w-6 h-6 text-indigo-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"
                />
              </svg>
              <h1 className="text-lg font-bold text-white tracking-tight">
                MCP Inspector
              </h1>
            </div>
            <span className="text-gray-600 text-sm hidden sm:inline">
              Real-time MCP debugger
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExport}
              disabled={events.length === 0}
              className="text-xs px-3 py-1 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Export JSON
            </button>
            <button
              onClick={clearEvents}
              disabled={events.length === 0}
              className="text-xs px-3 py-1 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Clear
            </button>
            <ConnectionStatus status={status} />
          </div>
        </div>
      </header>

      {/* Body: sidebar + main column */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar (US-006) */}
        <Sidebar
          events={events}
          selectedServer={filters.server}
          onSelectServer={handleSelectServer}
          open={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
        />

        {/* Main column */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Stats bar (US-005) */}
          <StatsBar events={events} />

          {/* Filter bar (US-004 + US-007) */}
          <FilterBar
            events={events}
            filteredCount={filteredEvents.length}
            filters={filters}
            onFilterChange={handleFilterChange}
            searchDisplay={searchDisplay}
            onSearchDisplayChange={setSearchDisplay}
            searchInputRef={searchInputRef}
          />

          {/* Event list */}
          <main className="flex-1 overflow-auto">
            <EventList
              events={filteredEvents}
              selectedEventId={selectedEvent?.id ?? null}
              onSelectEvent={handleSelectEvent}
            />
          </main>
        </div>
      </div>

      {/* Detail panel (US-008 copy buttons inside) */}
      <DetailPanel
        event={panelOpen ? selectedEvent : null}
        onClose={handleClosePanel}
      />
    </div>
  );
}
