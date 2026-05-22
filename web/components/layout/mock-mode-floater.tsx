"use client";

import { useState } from "react";
import { FlaskConical, X } from "lucide-react";

import { cn } from "@/lib/utils";

export function MockModeFloater() {
  const [hidden, setHidden] = useState(false);
  const enabled = process.env.NEXT_PUBLIC_MOCK_MODE === "true";
  if (!enabled || hidden) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "pointer-events-auto fixed bottom-20 right-3 z-40 md:bottom-3",
        "rounded-full border border-warning/40 bg-card/95 px-3 py-1.5",
        "shadow-md backdrop-blur supports-backdrop-filter:bg-card/80",
        "inline-flex items-center gap-2 text-[11px] text-warning",
      )}
    >
      <FlaskConical className="h-3.5 w-3.5" aria-hidden />
      <span className="tracking-wide">DEV · MOCK DATA</span>
      <button
        type="button"
        aria-label="关闭演示数据标识"
        onClick={() => setHidden(true)}
        className="ml-1 rounded-full p-0.5 hover:bg-warning/10"
      >
        <X className="h-3 w-3" aria-hidden />
      </button>
    </div>
  );
}
