"use client";

import type { McpEvent } from "@/types/events";

interface StatsBarProps {
  events: McpEvent[];
}

export function StatsBar({ events }: StatsBarProps) {
  const total = events.length;

  const responseEvents = events.filter(
    (e) => e.direction === "response" && e.latency_ms !== null
  );

  const avgLatency =
    responseEvents.length > 0
      ? Math.round(
          responseEvents.reduce((sum, e) => sum + (e.latency_ms ?? 0), 0) /
            responseEvents.length
        )
      : null;

  const errorCount = events.filter((e) => e.status === "error").length;
  const errorRate = total > 0 ? ((errorCount / total) * 100).toFixed(1) : null;

  return (
    <div className="border-b border-gray-800 bg-gray-900/30 px-5 py-2 flex items-center gap-6 flex-wrap">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">
          Total
        </span>
        <span className="font-semibold text-white">{total === 0 ? "—" : total}</span>
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">
          Avg Latency
        </span>
        <span className="font-semibold text-indigo-300">
          {avgLatency !== null ? `${avgLatency}ms` : "—"}
        </span>
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">
          Error Rate
        </span>
        <span
          className={`font-semibold ${
            errorRate !== null && parseFloat(errorRate) > 0
              ? "text-red-400"
              : "text-gray-300"
          }`}
        >
          {errorRate !== null ? `${errorRate}%` : "—"}
        </span>
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">
          Errors
        </span>
        <span
          className={`font-semibold ${
            errorCount > 0 ? "text-red-400" : "text-gray-300"
          }`}
        >
          {total === 0 ? "—" : errorCount}
        </span>
      </div>
    </div>
  );
}
