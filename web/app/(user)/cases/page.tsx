import type { Metadata } from "next";
import Link from "next/link";
import { FolderOpen, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MockBadge, WatermarkImage } from "@/components/yaoqi";
import { getCurrentUser } from "@/lib/auth";
import { serverApi } from "@/lib/api-server";
import {
  PURPOSE_OPTIONS,
  RISK_CLASS,
  RISK_LABEL,
  STATUS_LABEL,
  formatDateTime,
} from "@/lib/case-labels";
import type { CaseRecord, User } from "@/lib/types/domain";

export const metadata: Metadata = {
  title: "案例库 · 曜齐 YAOQI",
};

interface SearchParams {
  q?: string;
  purpose?: string;
  risk?: string;
  status?: string;
}

export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const sp = await searchParams;
  const user = (await getCurrentUser()) as User;

  const qs = new URLSearchParams();
  if (sp.q) qs.set("q", sp.q);
  // Select 的占位值是 "all",前端约定 "all" === 不筛选,不向后端传递
  if (sp.purpose && sp.purpose !== "all") qs.set("purpose", sp.purpose);
  if (sp.risk && sp.risk !== "all") qs.set("risk", sp.risk);
  if (sp.status && sp.status !== "all") qs.set("status", sp.status);

  const res = await serverApi.get<CaseRecord[]>(
    `/api/cases${qs.toString() ? `?${qs.toString()}` : ""}`,
  );
  const cases = res.data ?? [];

  const hasFilter =
    Boolean(sp.q) ||
    (sp.purpose && sp.purpose !== "all") ||
    (sp.risk && sp.risk !== "all") ||
    (sp.status && sp.status !== "all");

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-serif text-2xl">案例库</h1>
          <p className="mt-1 text-xs text-muted-foreground">
            按用途 / 风险 / 状态筛选,卡片支持点击进入详情。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <MockBadge status="mock" label="Mock 案例库" />
          <Button asChild className="cursor-pointer">
            <Link href="/cases/new">
              <Plus className="mr-1 h-4 w-4" aria-hidden />
              新建案例
            </Link>
          </Button>
        </div>
      </header>

      <Card className="p-3 md:p-4">
        <form
          method="GET"
          className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_repeat(3,180px)_auto]"
        >
          <Input
            name="q"
            placeholder="搜索案例编号 / 标题 / 品类"
            defaultValue={sp.q ?? ""}
          />
          <Select name="purpose" defaultValue={sp.purpose ?? "all"}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="用途" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部用途</SelectItem>
              {PURPOSE_OPTIONS.map((p) => (
                <SelectItem key={p} value={p}>
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select name="risk" defaultValue={sp.risk ?? "all"}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="风险" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部风险</SelectItem>
              <SelectItem value="low">低风险</SelectItem>
              <SelectItem value="medium">中风险</SelectItem>
              <SelectItem value="high">高风险</SelectItem>
            </SelectContent>
          </Select>
          <Select name="status" defaultValue={sp.status ?? "all"}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="draft">草稿</SelectItem>
              <SelectItem value="pending">待处理</SelectItem>
              <SelectItem value="analyzed">已分析</SelectItem>
              <SelectItem value="pending_recheck">待复检</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Button type="submit" className="cursor-pointer">
              筛选
            </Button>
            {hasFilter ? (
              <Button
                asChild
                type="button"
                variant="ghost"
                className="cursor-pointer text-xs"
              >
                <Link href="/cases">重置</Link>
              </Button>
            ) : null}
          </div>
        </form>
        <p className="mt-2 text-[11px] text-muted-foreground">
          注:Select 留空 / 选"全部"等同于不筛选;真实后端时支持时间范围筛选。
        </p>
      </Card>

      {cases.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-12 text-center">
          <FolderOpen
            className="mx-auto h-8 w-8 text-muted-foreground"
            aria-hidden
          />
          <p className="mt-3 text-sm text-muted-foreground">
            没有匹配的案例。换个筛选条件试试。
          </p>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cases.map((c) => (
            <li key={c.id}>
              <Link
                href={`/cases/${c.id}`}
                className="group block cursor-pointer space-y-3 rounded-lg border border-border bg-card/60 p-3 transition-colors hover:border-gold-antique/40"
              >
                <WatermarkImage
                  src={c.thumbnail}
                  alt={c.title}
                  caseNo={c.caseNo}
                  userSuffix={user.phoneSuffix}
                  ratio="video"
                />
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] tracking-wide text-muted-foreground">
                    <span>{c.caseNo}</span>
                    <span>{c.purpose}</span>
                  </div>
                  <h3 className="line-clamp-1 text-sm font-medium">{c.title}</h3>
                  <p className="line-clamp-2 text-xs text-muted-foreground">
                    {c.summary.materialHint}
                  </p>
                  <div className="flex items-center justify-between pt-1 text-[11px]">
                    <span
                      className={`rounded-full px-2 py-0.5 ring-1 ring-inset ${RISK_CLASS[c.risk]}`}
                    >
                      {RISK_LABEL[c.risk]}
                    </span>
                    <span className="text-muted-foreground">
                      {STATUS_LABEL[c.status]} · {formatDateTime(c.updatedAt)}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
