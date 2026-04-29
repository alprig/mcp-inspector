"use client";

import type { McpEvent } from "@/types/events";
import { ServerItem } from "./ServerItem";

interface SidebarProps {
  events: McpEvent[];
  selectedServer: string | null;
  onSelectServer: (server: string | null) => void;
  open: boolean;
  onToggle: () => void;
}

export function Sidebar({
  events,
  selectedServer,
  onSelectServer,
  open,
  onToggle,
}: SidebarProps) {
  // Build server list with request counts
  const serverMap = new Map<string, number>();
  for (const event of events) {
    serverMap.set(event.server, (serverMap.get(event.server) ?? 0) + 1);
  }
  const servers = Array.from(serverMap.entries()).sort((a, b) =>
    a[0].localeCompare(b[0])
  );

  const handleSelect = (name: string) => {
    onSelectServer(selectedServer === name ? null : name);
  };

  return (
    <>
      {/* Collapsed: just the toggle button visible */}
      {!open && (
        <div className="flex flex-col items-center py-3 border-r border-gray-800 bg-gray-900/60 w-10 shrink-0">
          <button
            onClick={onToggle}
            className="p-1.5 rounded text-gray-500 hover:text-white hover:bg-gray-700 transition-colors"
            aria-label="Open sidebar"
            title="Show server list"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          {selectedServer && (
            <div className="mt-2 w-2 h-2 rounded-full bg-indigo-500" title={selectedServer} />
          )}
        </div>
      )}

      {/* Expanded sidebar */}
      {open && (
        <aside className="hidden md:flex flex-col w-52 shrink-0 border-r border-gray-800 bg-gray-900/60 overflow-hidden">
          {/* Sidebar header */}
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-800">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Servers
            </span>
            <button
              onClick={onToggle}
              className="p-1 rounded text-gray-600 hover:text-white hover:bg-gray-700 transition-colors"
              aria-label="Close sidebar"
              title="Hide server list"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          </div>

          {/* Server list */}
          <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
            {servers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-gray-600">
                <svg
                  className="w-6 h-6 mb-2 opacity-40"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M5 12h14M12 5l7 7-7 7"
                  />
                </svg>
                <p className="text-xs text-center">No servers yet</p>
              </div>
            ) : (
              <>
                {/* "All" option */}
                {selectedServer !== null && (
                  <button
                    onClick={() => onSelectServer(null)}
                    className="w-full text-left px-3 py-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors rounded"
                  >
                    Show all
                  </button>
                )}
                {servers.map(([name, count]) => (
                  <ServerItem
                    key={name}
                    name={name}
                    requestCount={count}
                    isSelected={selectedServer === name}
                    onClick={() => handleSelect(name)}
                  />
                ))}
              </>
            )}
          </div>
        </aside>
      )}
    </>
  );
}
