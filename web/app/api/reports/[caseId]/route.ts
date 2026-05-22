import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { getCurrentUser } from "@/lib/auth";
import { cropReportForUser } from "@/lib/membership";
import reportsData from "@/lib/mock/reports.json";
import type { CaseReport, MembershipTier } from "@/lib/types/domain";

const reports = reportsData.reports as CaseReport[];

export async function GET(
  req: NextRequest,
  ctx: RouteContext<"/api/reports/[caseId]">,
) {
  const { caseId } = await ctx.params;
  const found = reports.find((r) => r.caseId === caseId);
  if (!found) {
    return NextResponse.json(
      { ok: false, error: "未找到报告", source: "mock" },
      { status: 404 },
    );
  }

  // 红线(UI-Spec §17.3):报告内容必须在服务端按当前会员裁剪后返回,
  // 不能由前端隐藏高级字段。
  const user = await getCurrentUser();
  const previewTier = req.nextUrl.searchParams.get("as") as MembershipTier | null;
  const tier: MembershipTier = previewTier ?? user?.membership ?? "free";

  const cropped = cropReportForUser(found, tier);
  return NextResponse.json({ ok: true, data: cropped, source: "mock" });
}
