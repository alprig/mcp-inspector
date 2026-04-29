"use client";

interface ServerItemProps {
  name: string;
  requestCount: number;
  isSelected: boolean;
  onClick: () => void;
}

export function ServerItem({
  name,
  requestCount,
  isSelected,
  onClick,
}: ServerItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2.5 rounded-md transition-colors flex items-center justify-between gap-2 ${
        isSelected
          ? "bg-indigo-600/20 border border-indigo-600/40 text-white"
          : "border border-transparent text-gray-400 hover:bg-gray-800 hover:text-white"
      }`}
    >
      <span className="text-xs font-medium truncate flex-1">{name}</span>
      <span
        className={`text-xs px-1.5 py-0.5 rounded font-mono ${
          isSelected
            ? "bg-indigo-600/30 text-indigo-300"
            : "bg-gray-800 text-gray-500"
        }`}
      >
        {requestCount}
      </span>
    </button>
  );
}
