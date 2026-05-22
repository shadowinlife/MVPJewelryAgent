import { Info } from "lucide-react";

import { cn } from "@/lib/utils";

type Variant = "inline" | "block";

const DEFAULT_LINES = [
  "AI 辅助判断，仅供参考，不构成交易承诺。",
  "建议结合线下复检与正式评估。",
  "高级价格内容需开通对应会员后查看。",
];

export function DisclaimerNote({
  lines = DEFAULT_LINES,
  variant = "block",
  className,
}: {
  lines?: string[];
  variant?: Variant;
  className?: string;
}) {
  if (variant === "inline") {
    return (
      <p
        className={cn(
          "inline-flex items-center gap-1 text-[11px] text-muted-foreground",
          className,
        )}
      >
        <Info className="h-3 w-3" aria-hidden />
        {lines[0]}
      </p>
    );
  }

  return (
    <aside
      role="note"
      aria-label="免责声明"
      className={cn(
        "rounded-md border border-dashed border-border bg-card/60 p-3 text-xs leading-relaxed text-muted-foreground",
        className,
      )}
    >
      <div className="mb-1 inline-flex items-center gap-1.5 text-[var(--color-tea-gray)]">
        <Info className="h-3.5 w-3.5" aria-hidden />
        <span className="text-[11px] tracking-wide uppercase">Disclaimer · 免责声明</span>
      </div>
      <ul className="space-y-1">
        {lines.map((line) => (
          <li key={line} className="flex items-start gap-1.5">
            <span aria-hidden className="mt-2 h-1 w-1 shrink-0 rounded-full bg-[var(--color-gold-soft)]" />
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
