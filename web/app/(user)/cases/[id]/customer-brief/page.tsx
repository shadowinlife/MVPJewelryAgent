import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Camera, Sparkles, TriangleAlert } from "lucide-react";

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
import type { CustomerBrief, User } from "@/lib/types/domain";

import { CopyBriefButton } from "./copy-brief-button";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  return { title: `客户简洁版 · ${id} · 曜齐 YAOQI` };
}

interface BriefPayload {
  caseId: string;
  caseNo: string;
  category: string;
  title: string;
  thumbnail: string;
  generatedAt: string;
  brief: CustomerBrief;
}

export default async function CustomerBriefPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = (await getCurrentUser()) as User;

  const res = await serverApi.get<BriefPayload>(`/api/customer-brief/${id}`);
  if (!res.ok || !res.data) notFound();
  const { caseNo, category, title, thumbnail, brief } = res.data;

  const copyText = buildCopyableBrief(caseNo, category, title, brief);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* 顶部:返回 + 标题 */}
      <div className="space-y-3">
        <Link
          href={`/cases/${id}`}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          返回完整报告
        </Link>
        <header className="flex flex-wrap items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
          <span>客户简洁版</span>
          <span>·</span>
          <span>{caseNo}</span>
          <MockBadge status="mock" label="Mock 简洁版" />
        </header>
        <h1 className="font-serif text-2xl">{title}</h1>
        <p className="text-xs text-muted-foreground">
          品类:{category} · 仅展示对客内容,不含内部价/策略/渠道。
        </p>
      </div>

      {/* 图片 */}
      <Card>
        <CardHeader className="pb-3">
          <CardDescription>实物图(水印预览)</CardDescription>
          <CardTitle className="font-serif text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mx-auto max-w-md">
            <WatermarkImage
              src={thumbnail}
              alt={title}
              caseNo={caseNo}
              userSuffix={user.phoneSuffix}
              ratio="square"
            />
          </div>
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            原图保留在工作台,不对外提供下载。
          </p>
        </CardContent>
      </Card>

      {/* 材质倾向 */}
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>材质倾向</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{brief.materialHint}</p>
        </CardContent>
      </Card>

      {/* 品质亮点 */}
      <Card>
        <CardHeader className="pb-2 flex flex-row items-center gap-2">
          <Sparkles
            className="h-4 w-4 text-gold-antique"
            aria-hidden
          />
          <CardTitle className="font-serif text-base">品质亮点</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
            {brief.qualityHighlights.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* 主要风险 + 复检建议 */}
      <Card>
        <CardHeader className="pb-2 flex flex-row items-center gap-2">
          <TriangleAlert
            className="h-4 w-4 text-warning"
            aria-hidden
          />
          <CardTitle className="font-serif text-base">注意事项</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <ul className="list-disc space-y-1.5 pl-5 leading-relaxed">
            {brief.mainRisks.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <div className="rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
            {brief.needReinspect
              ? "建议线下到正规机构复检后再做最终交易决定。"
              : "暂无紧急复检建议,如需大额交易仍可补充正规检测。"}
          </div>
        </CardContent>
      </Card>

      {/* 温和结论 */}
      <Card className="border-gold-antique/30">
        <CardHeader className="pb-2">
          <CardDescription>给客户的结论</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{brief.gentleConclusion}</p>
        </CardContent>
      </Card>

      <Separator />

      {/* 操作 */}
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <CopyBriefButton text={copyText} />
          <Button asChild variant="ghost" className="cursor-pointer">
            <Link href={`/cases/${id}`}>
              <ArrowLeft className="mr-1 h-4 w-4" aria-hidden />
              返回完整报告
            </Link>
          </Button>
        </div>
        <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <Camera className="h-3 w-3" aria-hidden />
          可截图发送给客户。本页不生成公开 URL,不提供分享按钮(UI-Spec §11.1)。
        </p>
      </div>

      <DisclaimerNote
        variant="block"
        lines={[
          "本简洁版基于 AI 辅助判断,仅供初步参考。",
          "建议在正规检测机构复检后再做交易决定。",
          "本平台不构成任何价格或品质的承诺。",
        ]}
      />
    </div>
  );
}

function buildCopyableBrief(
  caseNo: string,
  category: string,
  title: string,
  brief: CustomerBrief,
): string {
  const lines: string[] = [];
  lines.push(`【曜齐 YAOQI · ${caseNo}】${title}`);
  lines.push(`品类:${category}`);
  lines.push("");
  lines.push(`材质倾向:${brief.materialHint}`);
  lines.push("");
  lines.push("品质亮点:");
  brief.qualityHighlights.forEach((h) => lines.push(`· ${h}`));
  lines.push("");
  lines.push("注意事项:");
  brief.mainRisks.forEach((r) => lines.push(`· ${r}`));
  if (brief.needReinspect) {
    lines.push("· 建议线下到正规机构复检后再做最终交易决定");
  }
  lines.push("");
  lines.push(`结论:${brief.gentleConclusion}`);
  lines.push("");
  lines.push(
    "免责声明:本简洁版基于 AI 辅助判断,仅供初步参考,不构成交易承诺。",
  );
  return lines.join("\n");
}
