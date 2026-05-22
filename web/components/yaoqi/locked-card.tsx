import { Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LockedCard({
  title = "价格带与回收价为高级内容",
  description = "升级后可查看合理入手价、流通成交价、即时回收价和转售建议。",
  ctaLabel = "联系管理员开通",
  helperText = "AI 估价仅供参考，不替代线下复检和正式评估。",
  onCtaClick,
  className,
}: {
  title?: string;
  description?: string;
  ctaLabel?: string;
  helperText?: string;
  onCtaClick?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border border-[var(--color-gold-soft)]/60 bg-card/80 p-5",
        "shadow-[0_1px_0_color-mix(in_srgb,var(--color-gold-antique)_18%,transparent)]",
        className,
      )}
      data-locked="true"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_60%_at_0%_0%,color-mix(in_srgb,var(--color-gold-soft)_14%,transparent),transparent_60%)]"
      />
      <div className="relative flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[var(--color-gold-soft)]/60 bg-background/60 text-[var(--color-gold-antique)]">
          <Lock className="h-4 w-4" aria-hidden />
        </div>
        <div className="flex-1 space-y-3">
          <div>
            <h3 className="font-serif text-base text-foreground">{title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              {description}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={onCtaClick}
              className="border-[var(--color-gold-antique)]/70 text-[var(--color-gold-antique)] hover:bg-[color-mix(in_srgb,var(--color-gold-soft)_18%,transparent)] hover:text-[var(--color-gold-antique)]"
            >
              {ctaLabel}
            </Button>
            <span className="text-xs text-muted-foreground">{helperText}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
