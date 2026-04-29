"use client";

import { useState } from "react";

interface ReplayButtonProps {
  eventId: string;
}

type ReplayState = "idle" | "loading" | "success" | "error";

export function ReplayButton({ eventId }: ReplayButtonProps) {
  const [state, setState] = useState<ReplayState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleReplay = async () => {
    setState("loading");
    setErrorMessage(null);

    try {
      const res = await fetch(`http://localhost:8000/replay/${eventId}`, {
        method: "POST",
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        setErrorMessage(body.detail ?? `Request failed with status ${res.status}`);
        setState("error");
        return;
      }

      setState("success");
      setTimeout(() => {
        setState("idle");
      }, 1500);
    } catch {
      setErrorMessage("Network error — could not reach backend");
      setState("error");
    }
  };

  const isLoading = state === "loading";
  const isSuccess = state === "success";

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        onClick={handleReplay}
        disabled={isLoading}
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors
          ${isSuccess
            ? "bg-green-500/20 text-green-400 border border-green-500/40"
            : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 hover:bg-indigo-500/30 hover:text-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed"
          }`}
      >
        {isLoading ? (
          <>
            <svg
              className="w-3 h-3 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span>Replaying…</span>
          </>
        ) : isSuccess ? (
          <span>Sent!</span>
        ) : (
          <>
            <span>↺</span>
            <span>Replay</span>
          </>
        )}
      </button>

      {state === "error" && errorMessage && (
        <p className="text-xs text-red-400 max-w-[200px]">{errorMessage}</p>
      )}
    </div>
  );
}
