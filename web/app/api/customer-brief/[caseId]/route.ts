import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { getCurrentUser } from "@/lib/auth";
import casesData from "@/lib/mock/cases.json";
import reportsData from "@/lib/mock/reports.json";
import type {
  CaseRecord,
  CaseReport,
  CustomerBrief,
} from "@/lib/types/domain";

const cases = casesData.cases as CaseRecord[];
const reports = reportsData.reports as CaseReport[];

/**
 * 红线(UI-Spec §11.1, §17.3):
 *  - 只返回客户简洁版字段,内部价格/策略/渠道/相似案例/会员等级一律不出现在响应里;
 *  - 不生成公开 URL,接口需登录才能访问。
 */
export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/customer-brief/[caseId]">,
) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json(
      { ok: false, error: "未登录", source: "mock" },
      { status: 401 },
    );
  }

  const { caseId } = await ctx.params;
  const c = cases.find((it) => it.id === caseId);
  const report = reports.find((r) => r.caseId === caseId);
  if (!c || !report) {
    return NextResponse.json(
      { ok: false, error: "未找到客户简洁版", source: "mock" },
      { status: 404 },
    );
  }

  const brief: CustomerBrief = report.customerBrief;
  return NextResponse.json({
    ok: true,
    data: {
      caseId: c.id,
      caseNo: c.caseNo,
      category: c.category,
      title: c.title,
      thumbnail: c.thumbnail,
      generatedAt: report.generatedAt,
      brief,
    },
    source: "mock",
  });
}
