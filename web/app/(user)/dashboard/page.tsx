import type { Metadata } from "next";
import Link from "next/link";
import {
  Camera,
  FileText,
  Gavel,
  Sparkles,
  Tv,
  UploadCloud,
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
  MockBadge,
  WatermarkImage,
} from "@/components/yaoqi";
import { getCurrentUser } from "@/lib/auth";
import { serverApi } from "@/lib/api-server";
import { formatDateTime } from "@/lib/case-labels";
import { RISK_CLASS, RISK_LABEL, STATUS_LABEL } from "@/lib/case-labels";
import { getTierDef, tierLabel } from "@/lib/membership";
import type { CaseRecord, User } from "@/lib/types/domain";

export const metadata: Metadata = {
  title: "工作台 · 曜齐 YAOQI",
};

const ENTRY_CARDS = [
  {
    key: "upload",
    title: "上传珠宝图片",
    desc: "拍照 / 从相册导入,自动生成水印预览",
    icon: Camera,
    href: "/cases/new?step=basics",
  },
  {
    key: "cert",
    title: "上传证书识别",
    desc: "GIA / NGTC / 检测机构证书 OCR 识别",
    icon: FileText,
    href: "/cases/new?step=basics&kind=cert",
  },
  {
    key: "auction",
    title: "法拍评估",
    desc: "结合证书与现场照,提供风险上限建议",
    icon: Gavel,
    href: "/cases/new?step=basics&purpose=%E6%B3%95%E6%8B%8D",
  },
  {
    key: "live",
    title: "直播选品",
    desc: "快速判断材质 / 流通性,给出谈判要点",
    icon: Tv,
    href: "/cases/new?step=basics&purpose=%E7%9B%B4%E6%92%AD%E9%80%89%E5%93%81",
  },
  {
    key: "client",
    title: "客户咨询报告",
    desc: "为客户出具温和、不含内部价的简洁版",
    icon: Sparkles,
    href: "/cases/new?step=basics&purpose=%E5%AE%A2%E6%88%B7%E5%92%A8%E8%AF%A2",
  },
];

export default async function DashboardPage() {
  const user = (await getCurrentUser()) as User;
  const tierDef = getTierDef(user.membership);
  const casesRes = await serverApi.get<CaseRecord[]>("/api/cases");
  const recent = (casesRes.data ?? []).slice(0, 4);

  return (
    <div className="space-y-8">
      {/* 会员状态卡 */}
      <Card className="border-gold-antique/30">
        <CardHeader className="flex flex-row items-start justify-between gap-4 pb-3">
          <div className="space-y-1">
            <CardDescription>欢迎回来</CardDescription>
            <CardTitle className="font-serif text-2xl">
              {user.nickname}
            </CardTitle>
          </div>
          <MockBadge status="mock" label="Mock 会员体系" />
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <dt className="text-xs text-muted-foreground">当前会员</dt>
              <dd className="mt-0.5 text-gold-antique">
                {tierLabel(user.membership)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">月度配额</dt>
              <dd className="mt-0.5 font-medium">
                {tierDef.quotaHint}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">剩余报告次数</dt>
              <dd className="mt-0.5 font-medium">
                {user.remainingReports}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">到期</dt>
              <dd className="mt-0.5 font-medium">
                {user.membershipExpiresAt
                  ? formatDateTime(user.membershipExpiresAt)
                  : "—"}
              </dd>
            </div>
          </dl>
          <Separator className="my-4" />
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild className="cursor-pointer">
              <Link href="/cases/new">新建案例</Link>
            </Button>
            <Button asChild variant="outline" className="cursor-pointer">
              <Link href="/membership">查看会员权益</Link>
            </Button>
            <Button asChild variant="ghost" className="cursor-pointer text-xs">
              <Link href="/me">联系管理员开通</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 新建入口卡 */}
      <section className="space-y-3">
        <header className="flex items-baseline justify-between">
          <h2 className="font-serif text-lg">开始一次鉴定估价</h2>
          <Link
            href="/cases/new"
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            完整 5 步向导 →
          </Link>
        </header>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ENTRY_CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.key}
                href={card.href}
                className="group cursor-pointer rounded-lg border border-border bg-card/60 p-4 transition-colors hover:border-gold-antique/40 hover:bg-card"
              >
                <div className="mb-2 inline-flex h-9 w-9 items-center justify-center rounded-md bg-gold-antique/10 text-gold-antique">
                  <Icon className="h-4 w-4" aria-hidden />
                </div>
                <div className="text-sm font-medium">{card.title}</div>
                <p className="mt-1 text-xs text-muted-foreground">{card.desc}</p>
              </Link>
            );
          })}
          <div className="rounded-lg border border-dashed border-border p-4 text-xs text-muted-foreground">
            <UploadCloud
              className="mb-2 inline h-4 w-4 text-muted-foreground"
              aria-hidden
            />
            <p>批量上传与商家高级功能仅 {tierLabel("business_pro")} 可用。</p>
          </div>
        </div>
      </section>

      {/* 最近案例 */}
      <section className="space-y-3">
        <header className="flex items-baseline justify-between">
          <h2 className="font-serif text-lg">最近案例</h2>
          <Link
            href="/cases"
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            查看全部 →
          </Link>
        </header>

        {recent.length === 0 ? (
          <p className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            还没有案例。点击上方"新建案例"开始一次鉴定。
          </p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {recent.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/cases/${c.id}`}
                  className="group block cursor-pointer space-y-2 rounded-lg border border-border bg-card/60 p-3 transition-colors hover:border-gold-antique/40"
                >
                  <WatermarkImage
                    src={c.thumbnail}
                    alt={c.title}
                    caseNo={c.caseNo}
                    userSuffix={user.phoneSuffix}
                    ratio="square"
                  />
                  <div>
                    <div className="flex items-center justify-between text-[11px] tracking-wide text-muted-foreground">
                      <span>{c.caseNo}</span>
                      <span>{c.purpose}</span>
                    </div>
                    <div className="mt-1 line-clamp-1 text-sm font-medium">
                      {c.title}
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[11px]">
                      <span
                        className={`rounded-full px-2 py-0.5 ring-1 ring-inset ${RISK_CLASS[c.risk]}`}
                      >
                        {RISK_LABEL[c.risk]}
                      </span>
                      <span className="text-muted-foreground">
                        {STATUS_LABEL[c.status]}
                      </span>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <DisclaimerNote
        variant="block"
        lines={[
          "AI 输出仅供参考,不构成交易承诺。",
          "高价珠宝建议线下复检与正式评估。",
          "报告不等同于正式鉴定证书。",
        ]}
      />
    </div>
  );
}
