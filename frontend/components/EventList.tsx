"use client";

import type { McpEvent } from "@/types/events";
import { EventRow } from "./EventRow";

interface EventListProps {
  events: McpEvent[];
  selectedEventId: string | null;
  onSelectEvent: (event: McpEvent) => void;
}

export function EventList({
  events,
  selectedEventId,
  onSelectEvent,
}: EventListProps) {
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <svg
          className="w-12 h-12 mb-3 opacity-30"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <p className="text-sm">Waiting for MCP events…</p>
        <p className="text-xs mt-1 text-gray-600">
          Connect a MCP server and start making requests
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-700 bg-gray-800/50 sticky top-0 z-10">
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500 whitespace-nowrap">
              Time
            </th>
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Server
            </th>
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Tool / Method
            </th>
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Direction
            </th>
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th className="py-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500 text-right">
              Latency
            </th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <EventRow
              key={event.id}
              event={event}
              isSelected={event.id === selectedEventId}
              onClick={() => onSelectEvent(event)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
