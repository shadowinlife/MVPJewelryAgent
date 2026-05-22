import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, FileSignature } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MockBadge } from "@/components/yaoqi";
import { serverApi } from "@/lib/api-server";
import type { CaseRecord, OcrResult } from "@/lib/types/domain";

import { OcrEditor } from "./ocr-editor";

const STATUS_LABEL: Record<OcrResult["status"], string> = {
  pending: "等待上传证书",
  running: "OCR 识别中",
  succeeded: "OCR 识别成功",
  succeeded_with_low_confidence: "识别完成,存在低置信度字段",
  failed: "OCR 识别失败",
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  return { title: `证书 OCR · ${id} · 曜齐 YAOQI` };
}

export default async function CaseOcrPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const [caseRes, ocrRes] = await Promise.all([
    serverApi.get<CaseRecord>(`/api/cases/${id}`),
    serverApi.get<OcrResult>(`/api/ocr/${id}`),
  ]);
  if (!caseRes.ok || !caseRes.data) notFound();
  const c = caseRes.data;
  const ocr = ocrRes.ok ? ocrRes.data : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <Link
          href={`/cases/${id}`}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          返回案例详情
        </Link>
      </div>

      <header className="space-y-1">
        <div className="flex flex-wrap items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
          <FileSignature className="h-3.5 w-3.5" aria-hidden />
          <span>证书 OCR 确认</span>
          <span>·</span>
          <span>{c.caseNo}</span>
          <MockBadge status="mock" label="Mock OCR" />
        </div>
        <h1 className="font-serif text-2xl">{c.title}</h1>
        <p className="text-xs text-muted-foreground">
          逐字段核对识别结果。低置信度字段建议手动复核;字段修正后会以人工版本覆盖
          OCR 原值,进入后续 AI 报告。
        </p>
      </header>

      {ocr ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
          {/* 证书图片预览 */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>证书图片预览</CardDescription>
              <CardTitle className="font-serif text-base">
                {STATUS_LABEL[ocr.status]}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="aspect-3/4 w-full overflow-hidden rounded-md border border-border bg-muted/30">
                <Image
                  src={ocr.imageRef}
                  alt={`${c.title} 证书`}
                  width={480}
                  height={640}
                  className="h-full w-full object-contain"
                  unoptimized
                />
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">
                原图仅管理员可见(UI-Spec §12.3)。本页所示为水印预览版。
              </p>
            </CardContent>
          </Card>

          {/* 字段编辑 */}
          <OcrEditor
            caseId={c.id}
            caseNo={c.caseNo}
            initialFields={ocr.fields}
            rawText={ocr.rawText}
            status={STATUS_LABEL[ocr.status]}
          />
        </div>
      ) : (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            该案例还没有 OCR 结果。可以在「新建案例」流程中上传证书图片。
          </CardContent>
        </Card>
      )}
    </div>
  );
}
