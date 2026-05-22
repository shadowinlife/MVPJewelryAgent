import { NextResponse } from "next/server";

import casesData from "@/lib/mock/cases.json";
import type { CaseRecord } from "@/lib/types/domain";

const cases = casesData.cases as CaseRecord[];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const purpose = searchParams.get("purpose");
  const risk = searchParams.get("risk");
  const status = searchParams.get("status");
  const q = searchParams.get("q")?.trim().toLowerCase();

  const filtered = cases.filter((c) => {
    if (purpose && c.purpose !== purpose) return false;
    if (risk && c.risk !== risk) return false;
    if (status && c.status !== status) return false;
    if (q) {
      const hay = `${c.title} ${c.category} ${c.caseNo}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  return NextResponse.json({ ok: true, data: filtered, source: "mock" });
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as
    | Partial<CaseRecord>
    | null;

  if (!body?.title || !body?.category) {
    return NextResponse.json(
      { ok: false, error: "标题和品类必填", source: "mock" },
      { status: 400 },
    );
  }

  const draft: CaseRecord = {
    id: `case_draft_${Date.now()}`,
    caseNo: `YQ-DRAFT-${Date.now().toString().slice(-4)}`,
    ownerId: body.ownerId ?? "u_001",
    title: body.title,
    category: body.category,
    purpose: body.purpose ?? "鉴定",
    risk: body.risk ?? "low",
    status: "draft",
    source: "mock",
    thumbnail: "/mock/images/jadeite-bangle.svg",
    summary: body.summary ?? {
      materialHint: "待生成",
      liquidity: "待评估",
      needReinspect: false,
      membershipFloor: "free",
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  return NextResponse.json({ ok: true, data: draft, source: "mock" });
}
