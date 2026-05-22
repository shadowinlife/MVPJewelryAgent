import { MockBadge, type MockStatus } from "@/components/yaoqi/mock-badge";
import { cn } from "@/lib/utils";

export type StatusItem = {
  key: string;
  label: string;
  value: string;
  status: MockStatus;
};

export function StatusBar({
  items,
  className,
  dense = false,
}: {
  items: StatusItem[];
  className?: string;
  dense?: boolean;
}) {
  return (
    <dl
      className={cn(
        "flex flex-wrap items-stretch gap-2 rounded-md border border-border bg-card/60 p-2",
        dense ? "text-[11px]" : "text-xs",
        className,
      )}
      aria-label="接入状态"
    >
      {items.map((item) => (
        <div
          key={item.key}
          className={cn(
            "flex flex-1 min-w-[160px] items-center justify-between gap-3 rounded-sm bg-background/60 px-3",
            dense ? "py-1.5" : "py-2",
          )}
        >
          <div className="flex flex-col leading-tight">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {item.label}
            </dt>
            <dd className="font-medium text-foreground">{item.value}</dd>
          </div>
          <MockBadge status={item.status} />
        </div>
      ))}
    </dl>
  );
}
