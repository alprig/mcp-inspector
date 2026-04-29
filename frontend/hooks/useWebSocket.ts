"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { McpEvent, WsConnectionStatus, WsMessage } from "@/types/events";

const WS_URL = "ws://localhost:8000/ws";
const RECONNECT_DELAY_MS = 3000;
const MAX_EVENTS = 500;

interface UseWebSocketReturn {
  events: McpEvent[];
  status: WsConnectionStatus;
  clearEvents: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [events, setEvents] = useState<McpEvent[]>([]);
  const [status, setStatus] = useState<WsConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.CONNECTING ||
        wsRef.current.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    setStatus("connecting");

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      setStatus("connected");
    };

    ws.onmessage = (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const msg = JSON.parse(event.data as string) as WsMessage;
        if (msg.type === "event_created" || msg.type === "history") {
          setEvents((prev) => {
            const next = [msg.event, ...prev];
            return next.length > MAX_EVENTS ? next.slice(0, MAX_EVENTS) : next;
          });
        } else if (msg.type === "event_updated") {
          setEvents((prev) =>
            prev.map((e) => (e.id === msg.event.id ? msg.event : e)),
          );
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!isMountedRef.current) return;
      setStatus("disconnected");
      wsRef.current = null;
      reconnectTimerRef.current = setTimeout(() => {
        if (isMountedRef.current) connect();
      }, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, status, clearEvents };
}
