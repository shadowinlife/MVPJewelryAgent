import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import ocrData from "@/lib/mock/ocr-results.json";
import type { OcrResult } from "@/lib/types/domain";

const results = ocrData.ocrResults as OcrResult[];

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/ocr/[caseId]">,
) {
  const { caseId } = await ctx.params;
  const found = results.find((r) => r.caseId === caseId);
  if (!found) {
    return NextResponse.json(
      { ok: false, error: "未找到 OCR 结果", source: "mock" },
      { status: 404 },
    );
  }
  return NextResponse.json({ ok: true, data: found, source: "mock" });
}
