"use client";

import { useEffect, useCallback } from "react";
import type { McpEvent } from "@/types/events";
import { JsonViewer } from "./JsonViewer";
import { CopyButton } from "./CopyButton";

interface DetailPanelProps {
  event: McpEvent | null;
  onClose: () => void;
}

const statusColors: Record<McpEvent["status"], string> = {
  success: "text-green-400 bg-green-400/10 border border-green-400/30",
  error: "text-red-400 bg-red-400/10 border border-red-400/30",
  pending: "text-yellow-400 bg-yellow-400/10 border border-yellow-400/30",
};

export function DetailPanel({ event, onClose }: DetailPanelProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const isOpen = event !== null;

  const payloadJson = event
    ? JSON.stringify(event.payload, null, 2)
    : "";

  const metadataJson = event
    ? JSON.stringify(
        {
          id: event.id,
          method: event.method,
          direction: event.direction,
          server: event.server,
          tool: event.tool,
          status: event.status,
          latency_ms: event.latency_ms,
          timestamp: event.timestamp,
        },
        null,
        2
      )
    : "";

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-200 ${
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Slide-in panel */}
      <div
        className={`fixed top-0 right-0 h-full w-full max-w-2xl bg-gray-900 border-l border-gray-700 z-50 flex flex-col shadow-2xl transform transition-transform duration-200 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Event detail panel"
      >
        {event && (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700 shrink-0">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white text-sm">
                    {event.tool ?? event.method}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${statusColors[event.status]}`}
                  >
                    {event.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span>{event.server}</span>
                  <span>·</span>
                  <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                  {event.latency_ms !== null && (
                    <>
                      <span>·</span>
                      <span>{event.latency_ms}ms</span>
                    </>
                  )}
                  <span>·</span>
                  <span className="capitalize">{event.direction}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                aria-label="Close panel"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
              {/* Error section */}
              {event.status === "error" && (
                <section>
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-red-400 mb-2">
                    Error
                  </h2>
                  <div className="bg-red-900/20 border border-red-700/50 rounded p-3">
                    {typeof event.payload?.error === "object" &&
                    event.payload.error !== null ? (
                      <div className="flex flex-col gap-2">
                        {typeof (event.payload.error as Record<string, unknown>).message === "string" && (
                          <p className="text-red-300 text-sm font-medium">
                            {String((event.payload.error as Record<string, unknown>).message)}
                          </p>
                        )}
                        {typeof (event.payload.error as Record<string, unknown>).stack === "string" && (
                          <pre className="text-xs text-red-400/80 font-mono whitespace-pre-wrap">
                            {String((event.payload.error as Record<string, unknown>).stack)}
                          </pre>
                        )}
                      </div>
                    ) : typeof event.payload?.error === "string" ? (
                      <p className="text-red-300 text-sm">{event.payload.error}</p>
                    ) : (
                      <JsonViewer data={event.payload?.error ?? event.payload} />
                    )}
                  </div>
                </section>
              )}

              {/* Payload */}
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Payload
                  </h2>
                  <CopyButton value={payloadJson} />
                </div>
                <div className="bg-gray-800 rounded border border-gray-700 p-3">
                  <JsonViewer data={event.payload} />
                </div>
              </section>

              {/* Metadata */}
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Metadata
                  </h2>
                  <CopyButton value={metadataJson} />
                </div>
                <div className="bg-gray-800 rounded border border-gray-700 p-3">
                  <JsonViewer
                    data={{
                      id: event.id,
                      method: event.method,
                      direction: event.direction,
                      server: event.server,
                      tool: event.tool,
                      status: event.status,
                      latency_ms: event.latency_ms,
                      timestamp: event.timestamp,
                    }}
                  />
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </>
  );
}
