"use client";

import { useState } from "react";

interface CopyButtonProps {
  value: string;
}

export function CopyButton({ value }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard access denied — silent fail
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-0.5 rounded border border-gray-600 text-gray-400 hover:text-white hover:border-gray-500 transition-colors font-medium"
      aria-label={copied ? "Copied!" : "Copy to clipboard"}
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}
