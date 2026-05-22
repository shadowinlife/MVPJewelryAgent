import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import casesData from "@/lib/mock/cases.json";
import type { CaseRecord } from "@/lib/types/domain";

const cases = casesData.cases as CaseRecord[];

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/cases/[id]">,
) {
  const { id } = await ctx.params;
  const found = cases.find((c) => c.id === id || c.caseNo === id);
  if (!found) {
    return NextResponse.json(
      { ok: false, error: "案例不存在", source: "mock" },
      { status: 404 },
    );
  }
  return NextResponse.json({ ok: true, data: found, source: "mock" });
}
