import type { Metadata } from "next";
import Link from "next/link";
import {
  Bell,
  ChevronRight,
  FileText,
  HelpCircle,
  LogOut,
  Phone,
  Shield,
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
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { DisclaimerNote, MockBadge } from "@/components/yaoqi";
import { getCurrentUser } from "@/lib/auth";
import { formatDateTime } from "@/lib/case-labels";
import { getTierDef, tokenPolicy } from "@/lib/membership";
import type { User } from "@/lib/types/domain";

import { LogoutButton } from "@/components/layout/logout-button";

export const metadata: Metadata = {
  title: "我的 · 曜齐 YAOQI",
};

export default async function MePage() {
  const user = (await getCurrentUser()) as User;
  const tier = getTierDef(user.membership);

  // Mock: 把"剩余报告次数"和"月度配额"组合成可视化进度
  const usedReports = Math.max(tier.monthlyReportQuota - user.remainingReports, 0);
  const reportPct = Math.min(
    Math.round((usedReports / tier.monthlyReportQuota) * 100),
    100,
  );
  // Token 已用量在 mock 中没有真实数据,用一个比例(70% 剩余)推断
  const tokensRemaining = Math.round(tier.monthlyTokens * 0.7);
  const tokensUsed = tier.monthlyTokens - tokensRemaining;
  const tokenPct = Math.round((tokensUsed / tier.monthlyTokens) * 100);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-serif text-2xl">我的</h1>
        <p className="text-xs text-muted-foreground">
          账号信息、会员状态、配额、协议入口。
        </p>
      </header>

      {/* 账号信息 */}
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3 pb-3">
          <div className="space-y-1">
            <CardDescription>个人信息</CardDescription>
            <CardTitle className="font-serif text-xl">{user.nickname}</CardTitle>
          </div>
          <MockBadge status="mock" label="Mock 账号" />
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-3">
            <Item label="手机号" value={`****${user.phoneSuffix}`} icon={Phone} />
            <Item
              label="当前会员"
              value={tier.name}
              icon={Sparkles}
              accent
            />
            <Item
              label="到期时间"
              value={
                user.membershipExpiresAt
                  ? formatDateTime(user.membershipExpiresAt)
                  : "—"
              }
            />
            <Item label="注册时间" value={formatDateTime(user.createdAt)} />
            <Item label="最近登录" value={formatDateTime(user.lastLoginAt)} />
            <Item label="数据来源" value={user.source} />
          </dl>
        </CardContent>
      </Card>

      {/* 会员配额 */}
      <Card>
        <CardHeader className="pb-3">
          <CardDescription>本月用量</CardDescription>
          <CardTitle className="font-serif text-base">
            Token 配额每月 {tokenPolicy.resetDay} 号重置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5 text-sm">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Token 已用 / 月度配额</span>
              <span>
                {tokensUsed.toLocaleString()} / {tier.monthlyTokens.toLocaleString()}
              </span>
            </div>
            <Progress value={tokenPct} />
            <p className="text-[11px] text-muted-foreground">
              剩余约 {tokensRemaining.toLocaleString()} Token。
              {tokenPct >= 80 ? "本月配额即将用完,可联系管理员临时加量。" : null}
            </p>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>报告生成次数 已用 / 月度配额</span>
              <span>
                {usedReports} / {tier.monthlyReportQuota}
              </span>
            </div>
            <Progress value={reportPct} />
            <p className="text-[11px] text-muted-foreground">
              剩余 {user.remainingReports} 次。{tier.summary}
            </p>
          </div>

          <Separator />

          <div className="flex flex-wrap gap-2">
            <Button asChild className="cursor-pointer">
              <Link href="/membership">
                <Sparkles className="mr-1 h-4 w-4" aria-hidden />
                查看会员权益
              </Link>
            </Button>
            <Button asChild variant="outline" className="cursor-pointer">
              <Link href="/cases/new">
                <FileText className="mr-1 h-4 w-4" aria-hidden />
                新建案例
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 设置项 */}
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>设置</CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-border text-sm">
          <SettingRow
            icon={Bell}
            label="消息通知"
            hint="P1 功能,待接入"
            disabled
          />
          <SettingRow
            icon={Shield}
            label="隐私政策"
            hint="法务文案占位"
            href="#"
          />
          <SettingRow
            icon={FileText}
            label="用户协议"
            hint="法务文案占位"
            href="#"
          />
          <SettingRow
            icon={TriangleAlert}
            label="AI 辅助免责声明"
            hint="必须在生成报告前同意"
            href="#"
          />
          <SettingRow
            icon={HelpCircle}
            label="联系管理员开通"
            hint="升级会员 / 配额加量"
            href="#"
          />
        </CardContent>
      </Card>

      {/* 退出登录 */}
      <Card>
        <CardContent className="flex items-center justify-between py-4">
          <div className="space-y-0.5">
            <p className="text-sm">退出登录</p>
            <p className="text-[11px] text-muted-foreground">
              退出后需要重新使用手机号 + 验证码登录。
            </p>
          </div>
          <LogoutButton />
        </CardContent>
      </Card>

      <DisclaimerNote
        variant="block"
        lines={[
          "曜齐为珠宝鉴定辅助工具,AI 输出不构成最终交易承诺。",
          "如对账号、配额或开通有疑问,请联系管理员。",
        ]}
      />

      {/* 移动端登出兜底 */}
      <div className="md:hidden">
        <Button variant="ghost" className="w-full cursor-pointer text-danger">
          <LogOut className="mr-1 h-4 w-4" aria-hidden />
          登出
        </Button>
      </div>
    </div>
  );
}

function Item({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  icon?: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  accent?: boolean;
}) {
  return (
    <div>
      <dt className="flex items-center gap-1 text-xs text-muted-foreground">
        {Icon ? <Icon className="h-3.5 w-3.5" aria-hidden /> : null}
        <span>{label}</span>
      </dt>
      <dd
        className={`mt-0.5 ${accent ? "text-gold-antique" : "font-medium"}`}
      >
        {value}
      </dd>
    </div>
  );
}

function SettingRow({
  icon: Icon,
  label,
  hint,
  href,
  disabled,
}: {
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  label: string;
  hint: string;
  href?: string;
  disabled?: boolean;
}) {
  const inner = (
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-muted-foreground" aria-hidden />
        <div>
          <p className="text-sm">{label}</p>
          <p className="text-[11px] text-muted-foreground">{hint}</p>
        </div>
      </div>
      <ChevronRight
        className={`h-4 w-4 ${disabled ? "text-muted-foreground/50" : "text-muted-foreground"}`}
        aria-hidden
      />
    </div>
  );

  if (disabled || !href) {
    return (
      <div className={disabled ? "opacity-60" : undefined} aria-disabled={disabled}>
        {inner}
      </div>
    );
  }
  return (
    <Link href={href} className="block hover:bg-muted/30">
      {inner}
    </Link>
  );
}
