"use client";

import { useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ConnectionStatus } from "./ConnectionStatus";
import { EventList } from "./EventList";
import { DetailPanel } from "./DetailPanel";
import type { McpEvent } from "@/types/events";

export function Dashboard() {
  const { events, status, clearEvents } = useWebSocket();
  const [selectedEvent, setSelectedEvent] = useState<McpEvent | null>(null);

  const handleSelectEvent = (event: McpEvent) => {
    setSelectedEvent((prev) => (prev?.id === event.id ? null : event));
  };

  const handleClosePanel = () => setSelectedEvent(null);

  const successCount = events.filter((e) => e.status === "success").length;
  const errorCount = events.filter((e) => e.status === "error").length;
  const pendingCount = events.filter((e) => e.status === "pending").length;

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-30">
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
          <ConnectionStatus status={status} />
        </div>
      </header>

      {/* Stats bar */}
      <div className="border-b border-gray-800 bg-gray-900/50 px-5 py-2 flex items-center gap-6">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Total:</span>
          <span className="font-semibold text-white">{events.length}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-green-400 inline-block" />
          <span className="text-gray-400">
            {successCount} success
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-red-500 inline-block" />
          <span className="text-gray-400">
            {errorCount} error{errorCount !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-yellow-400 inline-block" />
          <span className="text-gray-400">
            {pendingCount} pending
          </span>
        </div>
        <div className="ml-auto">
          <button
            onClick={clearEvents}
            disabled={events.length === 0}
            className="text-xs px-3 py-1 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <EventList
          events={events}
          selectedEventId={selectedEvent?.id ?? null}
          onSelectEvent={handleSelectEvent}
        />
      </main>

      {/* Detail panel */}
      <DetailPanel event={selectedEvent} onClose={handleClosePanel} />
    </div>
  );
}
