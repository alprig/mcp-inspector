"use client";

import { useState } from "react";

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

interface JsonNodeProps {
  value: JsonValue;
  depth?: number;
  keyName?: string;
  isLast?: boolean;
}

function JsonNode({ value, depth = 0, keyName, isLast = true }: JsonNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const indent = depth * 16;

  const keyLabel = keyName !== undefined ? (
    <span className="text-blue-400">&quot;{keyName}&quot;</span>
  ) : null;

  const comma = isLast ? null : <span className="text-gray-400">,</span>;

  if (value === null) {
    return (
      <div style={{ paddingLeft: indent }} className="leading-5">
        {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
        <span className="text-red-400">null</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "boolean") {
    return (
      <div style={{ paddingLeft: indent }} className="leading-5">
        {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
        <span className="text-orange-400">{value ? "true" : "false"}</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "number") {
    return (
      <div style={{ paddingLeft: indent }} className="leading-5">
        {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
        <span className="text-green-400">{value}</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "string") {
    return (
      <div style={{ paddingLeft: indent }} className="leading-5 break-all">
        {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
        <span className="text-yellow-300">&quot;{value}&quot;</span>
        {comma}
      </div>
    );
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <div style={{ paddingLeft: indent }} className="leading-5">
          {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
          <span className="text-gray-400">[]</span>
          {comma}
        </div>
      );
    }

    return (
      <div style={{ paddingLeft: indent }}>
        <div className="leading-5 flex items-center gap-1">
          {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-gray-400 hover:text-white focus:outline-none select-none"
            aria-label={expanded ? "collapse" : "expand"}
          >
            {expanded ? "▼" : "▶"}
          </button>
          <span className="text-gray-400">[{expanded ? "" : `${value.length} items…`}]</span>
        </div>
        {expanded && (
          <>
            {value.map((item, idx) => (
              <JsonNode
                key={idx}
                value={item as JsonValue}
                depth={depth + 1}
                isLast={idx === value.length - 1}
              />
            ))}
            <div style={{ paddingLeft: 0 }} className="leading-5">
              <span className="text-gray-400">]</span>
              {comma}
            </div>
          </>
        )}
      </div>
    );
  }

  if (typeof value === "object") {
    const keys = Object.keys(value as Record<string, JsonValue>);
    if (keys.length === 0) {
      return (
        <div style={{ paddingLeft: indent }} className="leading-5">
          {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
          <span className="text-gray-400">{"{}"}</span>
          {comma}
        </div>
      );
    }

    return (
      <div style={{ paddingLeft: indent }}>
        <div className="leading-5 flex items-center gap-1">
          {keyLabel && <>{keyLabel}<span className="text-gray-400">: </span></>}
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-gray-400 hover:text-white focus:outline-none select-none"
            aria-label={expanded ? "collapse" : "expand"}
          >
            {expanded ? "▼" : "▶"}
          </button>
          <span className="text-gray-400">
            {"{"}
            {expanded ? "" : `${keys.length} keys…`}
            {expanded ? "" : "}"}
          </span>
        </div>
        {expanded && (
          <>
            {keys.map((k, idx) => (
              <JsonNode
                key={k}
                value={(value as Record<string, JsonValue>)[k]}
                depth={depth + 1}
                keyName={k}
                isLast={idx === keys.length - 1}
              />
            ))}
            <div style={{ paddingLeft: 0 }} className="leading-5">
              <span className="text-gray-400">{"}"}</span>
              {comma}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}

interface JsonViewerProps {
  data: unknown;
}

export function JsonViewer({ data }: JsonViewerProps) {
  return (
    <pre className="text-xs font-mono text-gray-200 overflow-auto">
      <JsonNode value={data as JsonValue} />
    </pre>
  );
}
