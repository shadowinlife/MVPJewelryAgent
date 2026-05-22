import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export type WizardStep = {
  key: string;
  label: string;
  description?: string;
};

export const NEW_CASE_STEPS: WizardStep[] = [
  { key: "basics", label: "基础信息", description: "用途 / 品类 / 心理价" },
  { key: "photos", label: "图片上传", description: "主图 / 细节 / 证书背景" },
  { key: "ocr", label: "OCR 确认", description: "证书识别核对" },
  { key: "supplement", label: "补充信息", description: "尺寸 / 重量 / 备注" },
  { key: "report", label: "生成报告", description: "确认并生成 AI 报告" },
];

export function WizardStepper({
  steps = NEW_CASE_STEPS,
  current,
  className,
}: {
  steps?: WizardStep[];
  current: number;
  className?: string;
}) {
  return (
    <ol
      className={cn(
        "flex w-full items-start gap-2 overflow-x-auto pb-1",
        className,
      )}
      aria-label="新建案例步骤"
    >
      {steps.map((step, idx) => {
        const state =
          idx < current ? "done" : idx === current ? "active" : "upcoming";
        const isLast = idx === steps.length - 1;
        return (
          <li
            key={step.key}
            className="flex min-w-[120px] flex-1 items-start gap-2"
            aria-current={state === "active" ? "step" : undefined}
          >
            <div className="flex flex-1 flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] font-medium transition-colors",
                    state === "done" &&
                      "border-[var(--color-gold-antique)] bg-[var(--color-gold-antique)] text-[var(--color-ivory)]",
                    state === "active" &&
                      "border-[var(--color-gold-antique)] bg-background text-[var(--color-gold-antique)]",
                    state === "upcoming" &&
                      "border-border bg-background text-muted-foreground",
                  )}
                >
                  {state === "done" ? (
                    <Check className="h-3.5 w-3.5" aria-hidden />
                  ) : (
                    idx + 1
                  )}
                </span>
                {!isLast ? (
                  <span
                    aria-hidden
                    className={cn(
                      "h-px flex-1 transition-colors",
                      idx < current
                        ? "bg-[var(--color-gold-antique)]"
                        : "bg-border",
                    )}
                  />
                ) : null}
              </div>
              <div className="space-y-0.5">
                <p
                  className={cn(
                    "text-xs font-medium",
                    state === "upcoming"
                      ? "text-muted-foreground"
                      : "text-foreground",
                  )}
                >
                  {step.label}
                </p>
                {step.description ? (
                  <p className="text-[10px] text-muted-foreground">
                    {step.description}
                  </p>
                ) : null}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
