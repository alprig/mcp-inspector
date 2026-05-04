"use client";

import { useState } from "react";
import type { McpEvent } from "@/types/events";
import { EventRow } from "./EventRow";

interface EventListProps {
  events: McpEvent[];
  selectedEventId: string | null;
  onSelectEvent: (event: McpEvent) => void;
}

function OnboardingGuide() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText("mcp-inspector setup").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="w-full max-w-[480px] rounded-xl border border-gray-700 bg-gray-900 p-6 space-y-5">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          Get Started
        </h2>

        {/* Step 1 */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-green-900/60 border border-green-700 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-white">Inspector is running</p>
            <p className="text-xs text-gray-500 mt-0.5">Dashboard is live at localhost:3333</p>
          </div>
        </div>

        {/* Step 2 */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center text-xs font-semibold text-gray-400">
            2
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">Run the setup command</p>
            <p className="text-xs text-gray-500 mt-0.5 mb-2">Wraps your MCP servers automatically</p>
            <div className="flex items-center gap-2 rounded-md bg-gray-800 border border-gray-700 px-3 py-2">
              <code className="flex-1 text-xs text-indigo-300 font-mono truncate">
                mcp-inspector setup
              </code>
              <button
                onClick={handleCopy}
                className="flex-shrink-0 text-xs px-2 py-0.5 rounded border border-gray-600 bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white transition-colors"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        </div>

        {/* Step 3 */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center text-xs font-semibold text-gray-400">
            3
          </div>
          <div>
            <p className="text-sm font-medium text-white">Restart Claude Code</p>
            <p className="text-xs text-gray-500 mt-0.5">Traffic will start appearing here automatically</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function EventList({
  events,
  selectedEventId,
  onSelectEvent,
}: EventListProps) {
  if (events.length === 0) {
    return <OnboardingGuide />;
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
