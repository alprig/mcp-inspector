"use client";

import type { WsConnectionStatus } from "@/types/events";

interface ConnectionStatusProps {
  status: WsConnectionStatus;
}

const statusConfig: Record<
  WsConnectionStatus,
  { label: string; dotClass: string; textClass: string }
> = {
  connected: {
    label: "Connected",
    dotClass: "bg-green-400 animate-pulse",
    textClass: "text-green-400",
  },
  disconnected: {
    label: "Disconnected",
    dotClass: "bg-red-500",
    textClass: "text-red-400",
  },
  connecting: {
    label: "Connecting…",
    dotClass: "bg-yellow-400 animate-pulse",
    textClass: "text-yellow-400",
  },
};

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${config.dotClass}`} />
      <span className={`text-sm font-medium ${config.textClass}`}>
        ws://localhost:8000/ws — {config.label}
      </span>
    </div>
  );
}
