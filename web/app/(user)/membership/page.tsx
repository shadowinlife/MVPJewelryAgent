import type { Metadata } from "next";
import Link from "next/link";
import { Check, Phone, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { DisclaimerNote, LockedCard, MockBadge } from "@/components/yaoqi";
import { getCurrentUser } from "@/lib/auth";
import { TIER_ORDER, tiers, tokenPolicy } from "@/lib/membership";
import type { MembershipTierDef, User } from "@/lib/types/domain";

export const metadata: Metadata = {
  title: "会员权益 · 曜齐 YAOQI",
};

const FIELD_LABELS: Record<string, string> = {
  materialHint: "材质倾向",
  risk: "风险等级",
  needReinspect: "复检建议",
  priceRange: "价格区间",
  liquidity: "流通性判断",
  recyclePrice: "即时回收价",
  fullRisk: "完整风险分析",
  negotiationStrategy: "压价策略",
  auctionCeiling: "法拍上限",
  channelHint: "渠道建议",
  similarCases: "内部相似案例",
  batchHint: "批量分析",
};

const ALL_FIELDS = [
  "materialHint",
  "risk",
  "needReinspect",
  "priceRange",
  "liquidity",
  "recyclePrice",
  "fullRisk",
  "negotiationStrategy",
  "auctionCeiling",
  "channelHint",
  "similarCases",
  "batchHint",
];

export default async function MembershipPage() {
  const user = (await getCurrentUser()) as User;
  const currentIdx = TIER_ORDER.indexOf(user.membership);
  const ordered: MembershipTierDef[] = TIER_ORDER.map(
    (k) => tiers.find((t) => t.key === k)!,
  );

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
          <Link href="/me" className="hover:text-foreground">
            我的
          </Link>
          <span>/</span>
          <span>会员权益</span>
          <MockBadge status="mock" label="Mock 会员体系" />
        </div>
        <h1 className="font-serif text-2xl">会员权益</h1>
        <p className="text-xs text-muted-foreground">
          5 档会员主要差别在月度 Token 配额与可见字段。升级请联系管理员。
        </p>
      </header>

      {/* 当前用户状态 */}
      <Card className="border-gold-antique/30 bg-gold-antique/5">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="text-xs text-muted-foreground">当前会员</p>
            <p className="font-serif text-xl text-gold-antique">
              {ordered[currentIdx]?.name ?? "—"}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {ordered[currentIdx]?.summary}
            </p>
          </div>
          <Button asChild className="cursor-pointer">
            <Link href="/me">
              <Phone className="mr-1 h-4 w-4" aria-hidden />
              联系管理员升级
            </Link>
          </Button>
        </CardContent>
      </Card>

      {/* 等级卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {ordered.map((t, idx) => {
          const isCurrent = t.key === user.membership;
          const isHigher = idx > currentIdx;
          const upcomingFields = idx === currentIdx + 1
            ? t.visibleFields.filter(
                (f) => !ordered[currentIdx]?.visibleFields.includes(f),
              )
            : [];

          return (
            <Card
              key={t.key}
              className={
                isCurrent
                  ? "border-gold-antique/50 bg-gold-antique/5"
                  : isHigher
                    ? "border-gold-antique/20"
                    : "border-border"
              }
            >
              <CardContent className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs text-muted-foreground">{t.priceHint}</p>
                    <p className="font-serif text-lg">{t.name}</p>
                  </div>
                  {isCurrent ? (
                    <span className="rounded-full bg-gold-antique/15 px-2 py-0.5 text-[10px] text-gold-antique ring-1 ring-inset ring-gold-antique/30">
                      当前等级
                    </span>
                  ) : isHigher ? (
                    <span className="rounded-full bg-muted/60 px-2 py-0.5 text-[10px] text-foreground/70">
                      升级可见
                    </span>
                  ) : (
                    <span className="rounded-full bg-muted/40 px-2 py-0.5 text-[10px] text-muted-foreground">
                      已包含
                    </span>
                  )}
                </div>

                <dl className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <dt className="text-muted-foreground">月度 Token</dt>
                    <dd className="font-medium">
                      {t.monthlyTokens.toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-muted-foreground">月度报告次数</dt>
                    <dd className="font-medium">{t.monthlyReportQuota}</dd>
                  </div>
                </dl>

                <Separator />

                <ul className="space-y-1.5 text-xs">
                  {ALL_FIELDS.map((f) => {
                    const included = t.visibleFields.includes(f);
                    const justAdded = upcomingFields.includes(f);
                    return (
                      <li
                        key={f}
                        className={`flex items-center gap-2 ${
                          included ? "text-foreground" : "text-muted-foreground/50"
                        }`}
                      >
                        <Check
                          className={`h-3.5 w-3.5 shrink-0 ${
                            included
                              ? "text-success"
                              : "text-muted-foreground/30"
                          }`}
                          aria-hidden
                        />
                        <span className="flex-1">{FIELD_LABELS[f] ?? f}</span>
                        {justAdded ? (
                          <span className="rounded-full bg-gold-antique/15 px-1.5 py-0.5 text-[10px] text-gold-antique">
                            升级新增
                          </span>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Token 政策说明 */}
      <Card>
        <CardContent className="p-4 text-sm">
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-gold-antique" aria-hidden />
            <span className="font-medium">Token 配额规则</span>
          </div>
          <ul className="ml-1 space-y-1.5 text-xs text-muted-foreground">
            <li>· 配额按自然月重置,每月 {tokenPolicy.resetDay} 号清零并按等级重新发放。</li>
            <li>· 超量后可联系管理员手动加量,不会自动扣费。</li>
            <li>· 不同案例的 Token 消耗会因图像数量、OCR 长度、AI 反复修正而浮动。</li>
            <li>· 客户简洁版仅基于已生成报告复用,不重复计费。</li>
          </ul>
        </CardContent>
      </Card>

      <LockedCard
        title="想了解定制商家方案?"
        description="如团队需要批量分析、内部相似案例或专属配额,可联系管理员定制。"
        ctaLabel="联系管理员洽谈"
      />

      <DisclaimerNote
        variant="block"
        lines={[
          "会员等级、Token 单价与可见字段在内测期间可能调整。",
          "AI 估价仅供参考,不替代正式鉴定证书与线下复检。",
        ]}
      />
    </div>
  );
}
