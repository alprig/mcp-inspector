"use client";

import { useRef } from "react";
import type { McpEvent } from "@/types/events";

type StatusFilter = McpEvent["status"] | null;

interface Filters {
  server: string | null;
  method: string | null;
  status: StatusFilter;
  searchQuery: string;
}

interface FilterBarProps {
  events: McpEvent[];
  filteredCount: number;
  filters: Filters;
  /** Committed search query (used by filteredEvents logic) */
  onFilterChange: (filters: Filters) => void;
  /** Display value for the search input (may be ahead of committed query) */
  searchDisplay: string;
  /** Called on every keystroke to update the display value */
  onSearchDisplayChange: (value: string) => void;
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
}

const STATUS_OPTIONS: Array<{ label: string; value: McpEvent["status"] | null }> = [
  { label: "All", value: null },
  { label: "Success", value: "success" },
  { label: "Error", value: "error" },
  { label: "Pending", value: "pending" },
];

const statusToggleClass: Record<string, string> = {
  null: "bg-indigo-600 text-white border-indigo-500",
  success: "bg-green-700 text-white border-green-600",
  error: "bg-red-700 text-white border-red-600",
  pending: "bg-yellow-600 text-white border-yellow-500",
};

export function FilterBar({
  events,
  filteredCount,
  filters,
  onFilterChange,
  searchDisplay,
  onSearchDisplayChange,
  searchInputRef,
}: FilterBarProps) {
  const uniqueServers = Array.from(new Set(events.map((e) => e.server))).sort();
  const uniqueMethods = Array.from(new Set(events.map((e) => e.method))).sort();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = (value: string) => {
    onSearchDisplayChange(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onFilterChange({ ...filters, searchQuery: value });
    }, 150);
  };

  const isFiltered =
    filters.server !== null ||
    filters.method !== null ||
    filters.status !== null ||
    filters.searchQuery !== "";

  const handleClear = () => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    onSearchDisplayChange("");
    onFilterChange({ server: null, method: null, status: null, searchQuery: "" });
  };

  const activeToggleKey = String(filters.status);

  return (
    <div className="border-b border-gray-800 bg-gray-900/20 px-5 py-2.5 flex items-center gap-3 flex-wrap">
      {/* Server dropdown */}
      <div className="flex items-center gap-1.5">
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium whitespace-nowrap">
          Server
        </label>
        <select
          value={filters.server ?? ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              server: e.target.value === "" ? null : e.target.value,
            })
          }
          className="text-xs bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="">All servers</option>
          {uniqueServers.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      {/* Method dropdown */}
      <div className="flex items-center gap-1.5">
        <label className="text-xs text-gray-500 uppercase tracking-wider font-medium whitespace-nowrap">
          Method
        </label>
        <select
          value={filters.method ?? ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              method: e.target.value === "" ? null : e.target.value,
            })
          }
          className="text-xs bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="">All methods</option>
          {uniqueMethods.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      {/* Status toggles */}
      <div className="flex items-center gap-1">
        {STATUS_OPTIONS.map((opt) => {
          const isActive = filters.status === opt.value;
          const activeClass =
            isActive ? statusToggleClass[activeToggleKey] : "";
          return (
            <button
              key={String(opt.value)}
              onClick={() =>
                onFilterChange({
                  ...filters,
                  status: isActive ? null : opt.value,
                })
              }
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                isActive
                  ? activeClass
                  : "border-gray-700 text-gray-400 hover:text-white hover:border-gray-600"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      <div className="w-px h-4 bg-gray-700 hidden sm:block" />

      {/* Search input (US-007) */}
      <div className="flex items-center gap-1.5 relative">
        <svg
          className="w-3.5 h-3.5 text-gray-500 absolute left-2 pointer-events-none"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          ref={searchInputRef}
          type="text"
          value={searchDisplay}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search events… (/)"
          className="text-xs bg-gray-800 border border-gray-700 text-gray-200 rounded pl-7 pr-6 py-1 w-48 focus:outline-none focus:border-indigo-500 placeholder-gray-600"
        />
        {searchDisplay && (
          <button
            onClick={() => handleSearchChange("")}
            className="absolute right-1.5 text-gray-500 hover:text-white transition-colors"
            aria-label="Clear search"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Showing X of Y */}
      {isFiltered && (
        <span className="text-xs text-gray-500">
          Showing{" "}
          <span className="text-white font-medium">{filteredCount}</span> of{" "}
          <span className="text-white font-medium">{events.length}</span>
        </span>
      )}

      {/* Clear filters */}
      {isFiltered && (
        <button
          onClick={handleClear}
          className="text-xs px-2.5 py-1 rounded border border-gray-700 text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
