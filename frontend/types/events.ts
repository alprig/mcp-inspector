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
}

export type WsConnectionStatus = "connected" | "disconnected" | "connecting";
