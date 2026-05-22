"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, ChevronDown, ChevronRight, Pencil, RefreshCw, Save, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { MockBadge } from "@/components/yaoqi";
import type { OcrConfidence, OcrField } from "@/lib/types/domain";

type EditState = "view" | "edit";

interface FieldRow extends OcrField {
  draft: string;
  dirty: boolean;
  state: EditState;
}

const CONF_CLASS: Record<OcrConfidence, string> = {
  high: "bg-success/10 text-success ring-success/20",
  medium: "bg-warning/10 text-warning ring-warning/30",
  low: "bg-danger/10 text-danger ring-danger/30",
};

const CONF_LABEL: Record<OcrConfidence, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

interface Props {
  caseId: string;
  caseNo: string;
  initialFields: OcrField[];
  rawText: string;
  status: string;
}

export function OcrEditor({ caseId, caseNo, initialFields, rawText, status }: Props) {
  const [rows, setRows] = useState<FieldRow[]>(
    initialFields.map((f) => ({
      ...f,
      draft: f.value,
      dirty: false,
      state: "view" as EditState,
    })),
  );
  const [rawOpen, setRawOpen] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggleEdit(key: string, target: EditState) {
    setRows((prev) =>
      prev.map((r) =>
        r.key === key
          ? {
              ...r,
              state: target,
              draft: target === "view" ? r.value : r.draft,
            }
          : r,
      ),
    );
  }

  function updateDraft(key: string, draft: string) {
    setRows((prev) =>
      prev.map((r) => (r.key === key ? { ...r, draft } : r)),
    );
  }

  function commitField(key: string) {
    setRows((prev) =>
      prev.map((r) =>
        r.key === key
          ? {
              ...r,
              value: r.draft,
              dirty: r.draft !== r.value || r.dirty,
              state: "view",
              // 用户改过的字段视为已修正,置信度提到 high
              confidence: r.draft !== r.value ? "high" : r.confidence,
            }
          : r,
      ),
    );
    setSaved(false);
  }

  function saveAll() {
    // Mock 保存:本轮只在前端做状态变更,真实接口接入后改为 POST /api/ocr/[caseId]
    setSaved(true);
    setRows((prev) => prev.map((r) => ({ ...r, dirty: false })));
  }

  const lowCount = rows.filter((r) => r.confidence === "low").length;
  const dirtyCount = rows.filter((r) => r.dirty).length;

  return (
    <div className="space-y-6">
      {/* 状态行 */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-muted/60 px-2 py-0.5 text-foreground/80">
          OCR 状态:{status}
        </span>
        <MockBadge status="mock" label="Mock OCR" />
        {lowCount > 0 ? (
          <span className="rounded-full bg-danger/10 px-2 py-0.5 text-danger ring-1 ring-inset ring-danger/30">
            {lowCount} 项低置信度需复核
          </span>
        ) : (
          <span className="rounded-full bg-success/10 px-2 py-0.5 text-success ring-1 ring-inset ring-success/20">
            所有字段置信度已达标
          </span>
        )}
      </div>

      {/* 字段卡片 */}
      <div className="space-y-2">
        {rows.map((row) => (
          <Card key={row.key} className="overflow-hidden">
            <CardContent className="flex flex-col gap-2 p-3 md:flex-row md:items-center md:gap-3">
              <div className="md:w-32 shrink-0">
                <div className="text-xs text-muted-foreground">{row.label}</div>
                <div className="mt-1 flex items-center gap-1.5">
                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[10px] ring-1 ring-inset ${CONF_CLASS[row.confidence]}`}
                  >
                    置信度 {CONF_LABEL[row.confidence]}
                  </span>
                  {row.dirty ? (
                    <span className="rounded-full bg-gold-antique/10 px-1.5 py-0.5 text-[10px] text-gold-antique ring-1 ring-inset ring-gold-antique/30">
                      已修正
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="flex-1">
                {row.state === "edit" ? (
                  <Input
                    value={row.draft}
                    onChange={(e) => updateDraft(row.key, e.target.value)}
                    autoFocus
                    aria-label={`编辑 ${row.label}`}
                  />
                ) : (
                  <div className="text-sm break-all">
                    {row.value || (
                      <span className="text-muted-foreground">— 未识别</span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex shrink-0 gap-1.5">
                {row.state === "edit" ? (
                  <>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => commitField(row.key)}
                      className="cursor-pointer"
                    >
                      <Check className="mr-1 h-3.5 w-3.5" aria-hidden />
                      确认
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleEdit(row.key, "view")}
                      className="cursor-pointer"
                    >
                      <X className="mr-1 h-3.5 w-3.5" aria-hidden />
                      取消
                    </Button>
                  </>
                ) : (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => toggleEdit(row.key, "edit")}
                    className="cursor-pointer"
                  >
                    <Pencil className="mr-1 h-3.5 w-3.5" aria-hidden />
                    编辑
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 原始 OCR 文本折叠 */}
      <Card>
        <CardHeader
          className="cursor-pointer select-none flex-row items-center justify-between gap-2 py-3"
          onClick={() => setRawOpen((o) => !o)}
        >
          <div className="flex items-center gap-2 text-sm">
            {rawOpen ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" aria-hidden />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" aria-hidden />
            )}
            <span>查看原始 OCR 文本</span>
          </div>
          <span className="text-[11px] text-muted-foreground">
            {rawOpen ? "点击收起" : "点击展开"}
          </span>
        </CardHeader>
        {rawOpen ? (
          <CardContent>
            <pre className="whitespace-pre-wrap rounded-md border border-border bg-muted/40 p-3 text-xs leading-relaxed text-foreground/80">
              {rawText}
            </pre>
          </CardContent>
        ) : null}
      </Card>

      <Separator />

      {/* 底部操作 */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            onClick={saveAll}
            disabled={dirtyCount === 0 && !saved}
            className="cursor-pointer"
          >
            <Save className="mr-1 h-4 w-4" aria-hidden />
            保存修正
            {dirtyCount > 0 ? `(${dirtyCount} 项)` : ""}
          </Button>
          <Button asChild className="cursor-pointer" variant="outline">
            <Link href={`/cases/${caseId}`}>
              <Check className="mr-1 h-4 w-4" aria-hidden />
              确认并返回案例
            </Link>
          </Button>
          <Button
            type="button"
            variant="ghost"
            className="cursor-pointer"
            disabled
          >
            <RefreshCw className="mr-1 h-4 w-4" aria-hidden />
            重新识别(P1,待接入)
          </Button>
        </div>
        {saved ? (
          <p className="text-xs text-success">
            已保存修正(Mock)。真实接口接入后会通过 POST /api/ocr/{caseNo} 持久化。
          </p>
        ) : null}
        <p className="text-[11px] text-muted-foreground">
          字段修正后会以人工录入信号覆盖原 OCR 值,并在后续 AI 报告中使用人工版本。
        </p>
      </div>
    </div>
  );
}
