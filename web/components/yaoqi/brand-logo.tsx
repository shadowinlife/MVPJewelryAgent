import { cn } from "@/lib/utils";

type Size = "sm" | "md" | "lg";

const sizeMap: Record<Size, { zh: string; en: string; gap: string }> = {
  sm: { zh: "text-lg", en: "text-[10px] tracking-[0.32em]", gap: "gap-0.5" },
  md: { zh: "text-2xl", en: "text-[11px] tracking-[0.4em]", gap: "gap-1" },
  lg: { zh: "text-3xl", en: "text-xs tracking-[0.45em]", gap: "gap-1.5" },
};

export function BrandLogo({
  size = "md",
  withTagline = false,
  className,
}: {
  size?: Size;
  withTagline?: boolean;
  className?: string;
}) {
  const s = sizeMap[size];

  return (
    <div
      className={cn(
        "inline-flex flex-col items-center font-serif text-foreground",
        s.gap,
        className,
      )}
      aria-label="曜齐 YAOQI"
    >
      <div className="inline-flex items-center gap-2">
        <span
          aria-hidden
          className="h-px w-6 bg-gradient-to-r from-transparent via-[var(--color-gold-antique)] to-[var(--color-gold-antique)]"
        />
        <span className={cn("font-medium tracking-[0.16em]", s.zh)}>曜齐</span>
        <span
          aria-hidden
          className="h-px w-6 bg-gradient-to-l from-transparent via-[var(--color-gold-antique)] to-[var(--color-gold-antique)]"
        />
      </div>
      <span
        className={cn(
          "uppercase text-[var(--color-gold-antique)]",
          s.en,
        )}
      >
        Yaoqi Atelier
      </span>
      {withTagline ? (
        <span className="mt-1 text-[10px] tracking-[0.25em] text-muted-foreground">
          玉石 · 珠宝 · 鉴定估价
        </span>
      ) : null}
    </div>
  );
}
