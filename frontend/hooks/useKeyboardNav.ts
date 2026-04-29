"use client";

import { useEffect } from "react";
import type { McpEvent } from "@/types/events";

interface UseKeyboardNavOptions {
  events: McpEvent[];
  selectedId: string | null;
  onSelect: (event: McpEvent) => void;
  onOpen: (event: McpEvent) => void;
  onClose: () => void;
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
}

function isInputFocused(): boolean {
  const tag = document.activeElement?.tagName?.toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select";
}

export function useKeyboardNav({
  events,
  selectedId,
  onSelect,
  onOpen,
  onClose,
  searchInputRef,
}: UseKeyboardNavOptions): void {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // "/" — focus search input (always intercept regardless of input focus)
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        searchInputRef?.current?.focus();
        return;
      }

      // All other shortcuts are disabled when an input is focused
      if (isInputFocused()) return;

      const currentIndex = selectedId
        ? events.findIndex((ev) => ev.id === selectedId)
        : -1;

      switch (e.key) {
        case "j":
        case "ArrowDown": {
          e.preventDefault();
          if (events.length === 0) return;
          const nextIndex =
            currentIndex < 0 ? 0 : Math.min(currentIndex + 1, events.length - 1);
          onSelect(events[nextIndex]);
          break;
        }
        case "k":
        case "ArrowUp": {
          e.preventDefault();
          if (events.length === 0) return;
          const prevIndex =
            currentIndex < 0
              ? events.length - 1
              : Math.max(currentIndex - 1, 0);
          onSelect(events[prevIndex]);
          break;
        }
        case "Enter": {
          e.preventDefault();
          if (currentIndex >= 0 && selectedId) {
            onOpen(events[currentIndex]);
          }
          break;
        }
        case "Escape": {
          onClose();
          break;
        }
        default:
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [events, selectedId, onSelect, onOpen, onClose, searchInputRef]);
}
