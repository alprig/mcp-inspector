export interface McpEvent {
  id: string;
  timestamp: string;
  server: string;
  tool: string | null;
  method: string;
  direction: "request" | "response";
  status: "success" | "error" | "pending";
  latency_ms: number | null;
  payload: Record<string, unknown>;
  request_id: string | null;
  replayed: boolean;
}

export interface WsMessage {
  type: "event_created" | "event_updated" | "history";
  event: McpEvent;
}

export type WsConnectionStatus = "connected" | "disconnected" | "connecting";
