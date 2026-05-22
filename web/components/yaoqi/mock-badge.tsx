import { cn } from "@/lib/utils";

export type MockStatus = "real" | "mock" | "pending" | "later";

const statusMap: Record<
  MockStatus,
  { label: string; cls: string; dot: string }
> = {
  real: {
    label: "真实可用",
    cls: "bg-[color-mix(in_srgb,var(--color-success)_12%,transparent)] text-[var(--color-success)] ring-[var(--color-success)]/30",
    dot: "bg-[var(--color-success)]",
  },
  mock: {
    label: "Mock 演示",
    cls: "bg-[color-mix(in_srgb,var(--color-warning)_14%,transparent)] text-[var(--color-warning)] ring-[var(--color-warning)]/30",
    dot: "bg-[var(--color-warning)]",
  },
  pending: {
    label: "待接入",
    cls: "bg-[color-mix(in_srgb,var(--color-neutral-warm)_18%,transparent)] text-[var(--color-tea-gray)] ring-[var(--color-neutral-warm)]/40",
    dot: "bg-[var(--color-neutral-warm)]",
  },
  later: {
    label: "后续版本",
    cls: "bg-[color-mix(in_srgb,var(--color-warm-gray)_40%,transparent)] text-[var(--color-tea-gray)] ring-[var(--color-warm-gray)]/60",
    dot: "bg-[var(--color-warm-gray)]",
  },
};

export function MockBadge({
  status,
  label,
  className,
}: {
  status: MockStatus;
  label?: string;
  className?: string;
}) {
  const s = statusMap[status];

  return (
    <span
      role="status"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide ring-1 ring-inset",
        s.cls,
        className,
      )}
    >
      <span aria-hidden className={cn("h-1.5 w-1.5 rounded-full", s.dot)} />
      {label ?? s.label}
    </span>
  );
}
