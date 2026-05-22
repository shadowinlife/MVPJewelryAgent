import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Copy,
  Edit2,
  FileSignature,
  RefreshCw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  DisclaimerNote,
  LockedCard,
  MockBadge,
  StatusBar,
  WatermarkImage,
} from "@/components/yaoqi";
import { getCurrentUser } from "@/lib/auth";
import { serverApi } from "@/lib/api-server";
import {
  RISK_CLASS,
  RISK_LABEL,
  STATUS_LABEL,
  formatDateTime,
} from "@/lib/case-labels";
import {
  TIER_ORDER,
  getTierDef,
  tierLabel,
  type CroppedReport,
} from "@/lib/membership";
import type { CaseRecord, OcrResult, User } from "@/lib/types/domain";

import { CopyReportButton } from "./copy-report-button";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  return { title: `案例 ${id} · 曜齐 YAOQI` };
}

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = (await getCurrentUser()) as User;

  const [caseRes, reportRes, ocrRes] = await Promise.all([
    serverApi.get<CaseRecord>(`/api/cases/${id}`),
    serverApi.get<CroppedReport>(`/api/reports/${id}`),
    serverApi.get<OcrResult>(`/api/ocr/${id}`),
  ]);

  if (!caseRes.ok || !caseRes.data) notFound();
  const c = caseRes.data;
  const report = reportRes.ok ? reportRes.data : null;
  const ocr = ocrRes.ok ? ocrRes.data : null;

  const userTierDef = getTierDef(user.membership);

  const reportText = report ? buildCopyableReport(c, report, user.nickname) : "";

  return (
    <div className="space-y-6">
      {/* 顶部摘要 */}
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
            <Link href="/cases" className="hover:text-foreground">
              案例库
            </Link>
            <span>/</span>
            <span>{c.caseNo}</span>
            <MockBadge status="mock" label="Mock 案例" />
            <span
              className={`rounded-full px-2 py-0.5 ring-1 ring-inset ${RISK_CLASS[c.risk]}`}
            >
              {RISK_LABEL[c.risk]}
            </span>
            <span className="rounded-full bg-muted/60 px-2 py-0.5 text-foreground/70">
              {STATUS_LABEL[c.status]}
            </span>
          </div>
          <h1 className="font-serif text-2xl">{c.title}</h1>
          <p className="text-xs text-muted-foreground">
            品类:{c.category} · 用途:{c.purpose} · 数据来源:{c.source} · 更新于{" "}
            {formatDateTime(c.updatedAt)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" className="cursor-pointer">
            <Link href={`/cases/${c.id}/ocr`}>
              <FileSignature className="mr-1 h-4 w-4" aria-hidden />
              证书 OCR
            </Link>
          </Button>
          <Button asChild className="cursor-pointer">
            <Link href={`/cases/${c.id}/customer-brief`}>
              <Sparkles className="mr-1 h-4 w-4" aria-hidden />
              客户简洁版
            </Link>
          </Button>
        </div>
      </header>

      {/* 模块接入状态 */}
      <StatusBar
        items={[
          { key: "case", label: "案例", value: STATUS_LABEL[c.status], status: "mock" },
          {
            key: "ocr",
            label: "OCR",
            value: ocr ? ocr.status : "未触发",
            status: "mock",
          },
          {
            key: "ai",
            label: "AI 报告",
            value: report ? "已生成" : "未生成",
            status: "mock",
          },
          { key: "img", label: "图片 OSS", value: "本地占位", status: "pending" },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* 主列 */}
        <div className="space-y-6">
          {/* 结论卡 */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>结论摘要</CardDescription>
              <CardTitle className="font-serif text-lg">
                {c.summary.materialHint}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <div>
                  <dt className="text-xs text-muted-foreground">风险等级</dt>
                  <dd className="mt-0.5">{RISK_LABEL[c.risk]}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">流通性</dt>
                  <dd className="mt-0.5">{c.summary.liquidity}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">是否建议复检</dt>
                  <dd className="mt-0.5">
                    {c.summary.needReinspect ? "是 · 建议线下复检" : "否"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">完整解锁</dt>
                  <dd className="mt-0.5">
                    {tierLabel(c.summary.membershipFloor)} 及以上
                  </dd>
                </div>
              </dl>
              {c.summary.needReinspect ? (
                <p className="flex items-start gap-2 rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
                  <TriangleAlert className="mt-0.5 h-3.5 w-3.5" aria-hidden />
                  当前案例风险敏感,强烈建议结合线下复检与正式评估。
                </p>
              ) : null}
            </CardContent>
          </Card>

          {/* 图片区 */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>图片资料</CardDescription>
              <CardTitle className="font-serif text-base">
                珠宝主图 / 证书图 / 上手图(水印预览)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {[c.thumbnail, c.thumbnail, c.thumbnail].map((src, i) => (
                  <div key={`${src}-${i}`} className="w-48 flex-shrink-0">
                    <WatermarkImage
                      src={src}
                      alt={`${c.title} 图 ${i + 1}`}
                      caseNo={c.caseNo}
                      userSuffix={user.phoneSuffix}
                      ratio={i === 1 ? "portrait" : "square"}
                    />
                  </div>
                ))}
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">
                普通用户不显示原图下载链接 · 原图仅管理员可见(UI-Spec §12.3)
              </p>
            </CardContent>
          </Card>

          {/* 报告区 */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-start justify-between gap-3">
              <div className="space-y-1">
                <CardDescription>AI 鉴定估价报告</CardDescription>
                <CardTitle className="font-serif text-base">
                  按当前会员 ·{" "}
                  <span className="text-gold-antique">
                    {userTierDef.name}
                  </span>{" "}
                  裁剪
                </CardTitle>
              </div>
              {report ? (
                <CopyReportButton text={reportText} />
              ) : null}
            </CardHeader>
            <CardContent className="space-y-4">
              {report ? (
                <ReportBody report={report} />
              ) : (
                <p className="text-sm text-muted-foreground">
                  暂无报告。可在"新建案例"流程的第 5 步生成。
                </p>
              )}
            </CardContent>
          </Card>

          {/* 底部操作 */}
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled className="cursor-not-allowed">
              <Edit2 className="mr-1 h-4 w-4" aria-hidden />
              编辑案例
            </Button>
            <Button variant="outline" disabled className="cursor-not-allowed">
              <RefreshCw className="mr-1 h-4 w-4" aria-hidden />
              重新生成报告
            </Button>
            <MockBadge status="later" label="P1 功能,待接入" />
          </div>
        </div>

        {/* 侧栏 */}
        <aside className="space-y-4">
          {/* 证书 OCR 摘要 */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>证书 OCR 摘要</CardDescription>
              <CardTitle className="font-serif text-base">关键字段</CardTitle>
            </CardHeader>
            <CardContent>
              {ocr && ocr.fields.length > 0 ? (
                <>
                  <ul className="space-y-1.5 text-sm">
                    {ocr.fields.slice(0, 6).map((f) => (
                      <li key={f.key} className="flex justify-between gap-2">
                        <span className="text-xs text-muted-foreground">
                          {f.label}
                        </span>
                        <span
                          className={`text-right ${
                            f.confidence === "low"
                              ? "text-warning"
                              : f.confidence === "medium"
                                ? "text-foreground/80"
                                : "text-foreground"
                          }`}
                        >
                          {f.value}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <Separator className="my-3" />
                  <Link
                    href={`/cases/${c.id}/ocr`}
                    className="text-xs text-gold-antique hover:underline"
                  >
                    人工确认 / 编辑 →
                  </Link>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">未识别到证书。</p>
              )}
            </CardContent>
          </Card>

          {/* 升级 / 客户简洁版入口 */}
          {report && report.lockedTiers.length > 0 ? (
            <LockedCard
              title={`${tierLabel(report.lockedTiers[0])} 起解锁更多分析`}
              description={`当前仅展示 ${tierLabel(user.membership)} 可见内容。升级后查看 ${report.lockedTiers.map(tierLabel).join(" / ")} 的高级字段。`}
            />
          ) : null}

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>给客户的简洁版</CardDescription>
              <CardTitle className="font-serif text-base">
                自动剔除内部价格与策略
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p className="text-muted-foreground">
                可复制或截图发给客户。不生成公开 URL,不带回收价/压价策略/法拍上限。
              </p>
              <Button asChild className="cursor-pointer" variant="outline">
                <Link href={`/cases/${c.id}/customer-brief`}>
                  <Sparkles className="mr-1 h-4 w-4" aria-hidden />
                  打开客户简洁版
                </Link>
              </Button>
            </CardContent>
          </Card>
        </aside>
      </div>

      <DisclaimerNote variant="block" />
    </div>
  );
}

function ReportBody({ report }: { report: CroppedReport }) {
  const v = report.visible;
  return (
    <div className="space-y-4 text-sm">
      <Section title="材质与基础结论">
        <Field label="材质倾向" value={v.materialHint} />
        <Field label="风险等级" value={v.risk} />
        <Field
          label="是否建议复检"
          value={
            v.needReinspect === undefined
              ? undefined
              : v.needReinspect
                ? "建议线下复检"
                : "暂无复检建议"
          }
        />
      </Section>
      <Section title="价格与流通(基础会员起)">
        <Field label="价格区间" value={v.priceRange} />
        <Field label="流通性" value={v.liquidity} />
      </Section>
      <Section title="深度分析(进阶会员起)">
        <Field label="即时回收价" value={v.recyclePrice} />
        {v.fullRisk ? (
          <Field label="完整风险" value={undefined}>
            <ul className="ml-1 list-disc space-y-0.5 pl-4">
              {v.fullRisk.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </Field>
        ) : (
          <Field label="完整风险" value={undefined} />
        )}
      </Section>
      <Section title="商家专属(商家会员起)">
        <Field label="压价策略" value={v.negotiationStrategy} />
        <Field label="法拍上限" value={v.auctionCeiling} />
        <Field label="渠道建议" value={v.channelHint} />
      </Section>
      <Section title="商家高级(批量与相似案例)">
        {v.similarCases ? (
          <Field label="相似历史案例" value={v.similarCases.join(", ")} />
        ) : (
          <Field label="相似历史案例" value={undefined} />
        )}
        <Field label="批量分析建议" value={v.batchHint} />
      </Section>

      {report.lockedTiers.length > 0 ? (
        <LockedCard
          title="更多高级分析需升级"
          description={`已锁定:${report.lockedTiers.map((t) => tierLabel(t)).join(" / ")}。升级会员后自动解锁。`}
        />
      ) : null}

      <p className="text-[11px] text-muted-foreground">
        当前可见等级:{tierLabel(report.userTier)}(共 {TIER_ORDER.length} 档)
      </p>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-md border border-border bg-card/40 p-3">
      <div className="mb-2 text-[11px] tracking-wide uppercase text-muted-foreground">
        {title}
      </div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
  children,
}: {
  label: string;
  value: string | undefined;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-0.5 text-sm md:flex-row md:items-start md:gap-3">
      <span className="w-28 shrink-0 text-xs text-muted-foreground">{label}</span>
      {children ? (
        <div className="flex-1">{children}</div>
      ) : (
        <span className={value ? "flex-1" : "flex-1 text-muted-foreground"}>
          {value ?? "— 当前会员暂不可见"}
        </span>
      )}
    </div>
  );
}

function buildCopyableReport(
  c: CaseRecord,
  report: CroppedReport,
  nickname: string,
): string {
  const lines: string[] = [];
  lines.push(`【曜齐 YAOQI · ${c.caseNo}】${c.title}`);
  lines.push(`品类:${c.category} · 用途:${c.purpose}`);
  lines.push(`鉴定时间:${formatDateTime(report.generatedAt)}`);
  lines.push(`阅读用户:${nickname}(${tierLabel(report.userTier)})`);
  lines.push("");
  const v = report.visible;
  if (v.materialHint) lines.push(`材质倾向:${v.materialHint}`);
  if (v.risk) lines.push(`风险等级:${v.risk}`);
  if (v.priceRange) lines.push(`价格区间:${v.priceRange}`);
  if (v.liquidity) lines.push(`流通性:${v.liquidity}`);
  if (v.recyclePrice) lines.push(`回收参考:${v.recyclePrice}`);
  if (v.negotiationStrategy) lines.push(`压价策略:${v.negotiationStrategy}`);
  if (v.auctionCeiling) lines.push(`法拍上限:${v.auctionCeiling}`);
  if (v.channelHint) lines.push(`渠道建议:${v.channelHint}`);
  lines.push("");
  lines.push("免责声明:AI 辅助判断,仅供参考,不构成交易承诺。");
  return lines.join("\n");
}
