"use client";

import type { McpEvent } from "@/types/events";

interface EventRowProps {
  event: McpEvent;
  isSelected: boolean;
  onClick: () => void;
}

const statusDot: Record<McpEvent["status"], string> = {
  success: "bg-green-400",
  error: "bg-red-500",
  pending: "bg-yellow-400",
};

const statusText: Record<McpEvent["status"], string> = {
  success: "text-green-400",
  error: "text-red-400",
  pending: "text-yellow-400",
};

const directionBadge: Record<McpEvent["direction"], string> = {
  request: "bg-blue-900/50 text-blue-300 border border-blue-700/50",
  response: "bg-purple-900/50 text-purple-300 border border-purple-700/50",
};

export function EventRow({ event, isSelected, onClick }: EventRowProps) {
  const time = new Date(event.timestamp).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const timeMs = new Date(event.timestamp).getMilliseconds();
  const timeFull = `${time}.${String(timeMs).padStart(3, "0")}`;

  return (
    <tr
      onClick={onClick}
      className={`cursor-pointer border-b border-gray-800 transition-colors hover:bg-gray-800/60 ${
        isSelected ? "bg-gray-800" : ""
      }`}
    >
      {/* Time */}
      <td className="py-2.5 px-3 text-xs font-mono text-gray-400 whitespace-nowrap">
        {timeFull}
      </td>

      {/* Server */}
      <td className="py-2.5 px-3 text-xs text-gray-300 whitespace-nowrap max-w-[120px] truncate">
        {event.server}
      </td>

      {/* Tool / Method */}
      <td className="py-2.5 px-3 text-xs text-white whitespace-nowrap max-w-[180px] truncate">
        <span>{event.tool ?? event.method}</span>
        {event.replayed && (
          <span className="ml-1.5 text-xs text-indigo-400 font-medium">↺</span>
        )}
      </td>

      {/* Direction */}
      <td className="py-2.5 px-3">
        <span
          className={`text-xs px-2 py-0.5 rounded font-medium ${directionBadge[event.direction]}`}
        >
          {event.direction}
        </span>
      </td>

      {/* Status */}
      <td className="py-2.5 px-3">
        <div className="flex items-center gap-1.5">
          <span
            className={`inline-block h-2 w-2 rounded-full ${statusDot[event.status]}`}
          />
          <span className={`text-xs font-medium ${statusText[event.status]}`}>
            {event.status}
          </span>
        </div>
      </td>

      {/* Latency */}
      <td className="py-2.5 px-3 text-xs text-gray-400 text-right whitespace-nowrap">
        {event.latency_ms !== null ? `${Math.round(event.latency_ms)}ms` : "—"}
      </td>
    </tr>
  );
}
