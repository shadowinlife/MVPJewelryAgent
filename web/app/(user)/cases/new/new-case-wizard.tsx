"use client";

import { useMemo, useState, type ChangeEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Camera,
  Check,
  FileText,
  ImagePlus,
  Save,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  MockBadge,
  NEW_CASE_STEPS,
  WizardStepper,
} from "@/components/yaoqi";
import { CATEGORY_OPTIONS, PURPOSE_OPTIONS } from "@/lib/case-labels";

interface Props {
  initialStep: string;
  initialPurpose: string;
  initialKind: string;
  remainingReports: number;
  monthlyTokens: number;
  tierLabel: string;
  tokenResetDay: number;
}

interface FormState {
  category: string;
  purpose: string;
  sourceChannel: string;
  intent: string;
  hasCert: boolean;
  size: string;
  weight: string;
  certAgency: string;
  certNo: string;
  askingPrice: string;
  psychPrice: string;
  sellerCopy: string;
  notes: string;
  intents: string[];
}

const SOURCE_OPTIONS = ["朋友寄售", "直播抢拍", "二手平台", "线下拍卖", "客户咨询", "其他"];
const INTENT_OPTIONS = ["出售", "回收", "寄售", "持有", "再加工"];

const STEP_KEYS = ["basics", "photos", "ocr", "supplement", "report"] as const;
type StepKey = (typeof STEP_KEYS)[number];

const ESTIMATED_TOKENS = 3500;

export function NewCaseWizard({
  initialStep,
  initialPurpose,
  initialKind,
  remainingReports,
  monthlyTokens,
  tierLabel,
  tokenResetDay,
}: Props) {
  const router = useRouter();
  const startIdx = Math.max(
    0,
    STEP_KEYS.indexOf((initialStep as StepKey) ?? "basics"),
  );
  const [stepIdx, setStepIdx] = useState(startIdx);
  const [draftSaved, setDraftSaved] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [form, setForm] = useState<FormState>({
    category: "",
    purpose: initialPurpose,
    sourceChannel: "",
    intent: "",
    hasCert: initialKind === "cert",
    size: "",
    weight: "",
    certAgency: "",
    certNo: "",
    askingPrice: "",
    psychPrice: "",
    sellerCopy: "",
    notes: "",
    intents: [],
  });

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setDraftSaved(false);
  }

  function toggleIntent(option: string, checked: boolean) {
    setForm((prev) => ({
      ...prev,
      intents: checked
        ? Array.from(new Set([...prev.intents, option]))
        : prev.intents.filter((x) => x !== option),
    }));
    setDraftSaved(false);
  }

  function saveDraft() {
    // Mock 草稿:本轮只在前端记忆。真实接口接入后改为 POST /api/cases (status=draft)。
    setDraftSaved(true);
  }

  function generateReport() {
    // Mock 生成:本轮直接跳已存在的演示案例
    setGenerated(true);
    setTimeout(() => router.push("/cases/case_2026_0001"), 600);
  }

  const canForward = useMemo(() => {
    if (stepIdx === 0) return form.category && form.purpose;
    return true;
  }, [stepIdx, form.category, form.purpose]);

  function goNext() {
    if (stepIdx < STEP_KEYS.length - 1) setStepIdx((i) => i + 1);
  }
  function goPrev() {
    if (stepIdx > 0) setStepIdx((i) => i - 1);
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
          <Link href="/dashboard" className="hover:text-foreground">
            工作台
          </Link>
          <span>/</span>
          <span>新建案例</span>
          <MockBadge status="mock" label="Mock 流程" />
        </div>
        <h1 className="font-serif text-2xl">新建一次鉴定估价</h1>
        <p className="text-xs text-muted-foreground">
          按 5 步完成基础录入。每步信息少而集中,可随时保存草稿。
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <WizardStepper steps={NEW_CASE_STEPS} current={stepIdx} />
        </CardContent>
      </Card>

      {/* 步骤内容 */}
      {STEP_KEYS[stepIdx] === "basics" ? (
        <StepBasics form={form} update={update} />
      ) : null}
      {STEP_KEYS[stepIdx] === "photos" ? (
        <StepPhotos hasCert={form.hasCert} setHasCert={(v) => update("hasCert", v)} />
      ) : null}
      {STEP_KEYS[stepIdx] === "ocr" ? <StepOcr hasCert={form.hasCert} /> : null}
      {STEP_KEYS[stepIdx] === "supplement" ? (
        <StepSupplement form={form} update={update} toggleIntent={toggleIntent} />
      ) : null}
      {STEP_KEYS[stepIdx] === "report" ? (
        <StepReport
          tierLabel={tierLabel}
          remainingReports={remainingReports}
          monthlyTokens={monthlyTokens}
          tokenResetDay={tokenResetDay}
          generated={generated}
          onGenerate={generateReport}
        />
      ) : null}

      <Separator />

      {/* 底部操作 */}
      <div className="sticky bottom-4 z-10 rounded-lg border border-border bg-background/80 p-3 supports-backdrop-filter:bg-background/70 supports-backdrop-filter:backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex gap-2">
            <Button
              type="button"
              variant="ghost"
              className="cursor-pointer"
              onClick={goPrev}
              disabled={stepIdx === 0}
            >
              <ArrowLeft className="mr-1 h-4 w-4" aria-hidden />
              上一步
            </Button>
            <Button
              type="button"
              variant="outline"
              className="cursor-pointer"
              onClick={saveDraft}
            >
              <Save className="mr-1 h-4 w-4" aria-hidden />
              保存草稿
            </Button>
          </div>
          <div className="flex items-center gap-2">
            {draftSaved ? (
              <span className="text-xs text-success">草稿已保存(Mock)</span>
            ) : null}
            {stepIdx < STEP_KEYS.length - 1 ? (
              <Button
                type="button"
                className="cursor-pointer"
                onClick={goNext}
                disabled={!canForward}
              >
                下一步
                <ArrowRight className="ml-1 h-4 w-4" aria-hidden />
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ----- 步骤 1: 基础信息 ----- */
function StepBasics({
  form,
  update,
}: {
  form: FormState;
  update: <K extends keyof FormState>(k: K, v: FormState[K]) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardDescription>第 1 步</CardDescription>
        <CardTitle className="font-serif text-base">基础信息</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label>品类 *</Label>
          <Select value={form.category} onValueChange={(v) => update("category", v ?? "")}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="选择品类" />
            </SelectTrigger>
            <SelectContent>
              {CATEGORY_OPTIONS.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label>用途 *</Label>
          <Select value={form.purpose} onValueChange={(v) => update("purpose", v ?? "")}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="选择用途" />
            </SelectTrigger>
            <SelectContent>
              {PURPOSE_OPTIONS.map((p) => (
                <SelectItem key={p} value={p}>
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label>来源渠道</Label>
          <Select
            value={form.sourceChannel}
            onValueChange={(v) => update("sourceChannel", v ?? "")}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="如:朋友寄售" />
            </SelectTrigger>
            <SelectContent>
              {SOURCE_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="intent">意向(可选)</Label>
          <Input
            id="intent"
            placeholder="如:打算谈到 1.6 万以下"
            value={form.intent}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              update("intent", e.target.value)
            }
          />
        </div>
      </CardContent>
    </Card>
  );
}

/* ----- 步骤 2: 图片上传(Mock) ----- */
function StepPhotos({
  hasCert,
  setHasCert,
}: {
  hasCert: boolean;
  setHasCert: (v: boolean) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardDescription>第 2 步</CardDescription>
        <CardTitle className="font-serif text-base">图片上传</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          {["珠宝自然光图", "打灯图", "上手图"].map((label) => (
            <UploadSlot key={label} label={label} />
          ))}
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {["背面图", "瑕疵图", "卖家文案截图"].map((label) => (
            <UploadSlot key={label} label={label} />
          ))}
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <Checkbox
            checked={hasCert}
            onCheckedChange={(v) => setHasCert(v === true)}
          />
          <span>本次包含证书图,需要进入 OCR 识别</span>
        </label>
        <p className="text-[11px] text-muted-foreground">
          Mock 阶段不真实上传文件,点击插槽仅模拟成功。真实环境会上传到 OSS,
          展示水印预览图,原图不直接对外提供。
        </p>
      </CardContent>
    </Card>
  );
}

function UploadSlot({ label }: { label: string }) {
  const [filled, setFilled] = useState(false);
  return (
    <button
      type="button"
      onClick={() => setFilled(true)}
      className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1.5 rounded-md border border-dashed border-border bg-card/40 p-3 text-xs text-muted-foreground transition-colors hover:border-gold-antique/60 hover:text-foreground"
    >
      {filled ? (
        <>
          <Check className="h-5 w-5 text-success" aria-hidden />
          <span>{label} · 已上传(Mock)</span>
        </>
      ) : (
        <>
          <ImagePlus className="h-5 w-5" aria-hidden />
          <span>{label}</span>
          <span className="text-[10px]">点击模拟上传</span>
        </>
      )}
    </button>
  );
}

/* ----- 步骤 3: OCR 确认(占位) ----- */
function StepOcr({ hasCert }: { hasCert: boolean }) {
  return (
    <Card>
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div>
          <CardDescription>第 3 步</CardDescription>
          <CardTitle className="font-serif text-base">OCR 确认</CardTitle>
        </div>
        <MockBadge status="mock" label="Mock OCR" />
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {hasCert ? (
          <>
            <p>
              证书识别将在生成报告前自动完成,本步骤用于核对结果。Mock 阶段直接通过即可,
              生成案例后可在「证书 OCR」页面修正字段。
            </p>
            <div className="rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
              低置信度字段建议进入案例后逐项复核,以免错值进入 AI 报告。
            </div>
          </>
        ) : (
          <p className="text-muted-foreground">
            未勾选证书图,跳过 OCR。如需补充证书,可在第 2 步勾上「包含证书图」。
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/* ----- 步骤 4: 补充信息 ----- */
function StepSupplement({
  form,
  update,
  toggleIntent,
}: {
  form: FormState;
  update: <K extends keyof FormState>(k: K, v: FormState[K]) => void;
  toggleIntent: (opt: string, checked: boolean) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardDescription>第 4 步</CardDescription>
        <CardTitle className="font-serif text-base">补充信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <TextField
            label="尺寸"
            id="size"
            value={form.size}
            placeholder="如:内径 56mm"
            onChange={(v) => update("size", v)}
          />
          <TextField
            label="重量"
            id="weight"
            value={form.weight}
            placeholder="如:56.3 g"
            onChange={(v) => update("weight", v)}
          />
          <TextField
            label="证书机构"
            id="cert-agency"
            value={form.certAgency}
            placeholder="如:NGTC / GIA"
            onChange={(v) => update("certAgency", v)}
          />
          <TextField
            label="证书编号"
            id="cert-no"
            value={form.certNo}
            placeholder="证书号"
            onChange={(v) => update("certNo", v)}
          />
          <TextField
            label="叫价 / 起拍价"
            id="asking"
            value={form.askingPrice}
            placeholder="如:25,000 元"
            onChange={(v) => update("askingPrice", v)}
          />
          <TextField
            label="心理价(选填,不会出现在客户简洁版)"
            id="psych"
            value={form.psychPrice}
            placeholder="如:18,000 元"
            onChange={(v) => update("psychPrice", v)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="seller-copy">卖家文案 / 直播话术摘录(可选)</Label>
          <Textarea
            id="seller-copy"
            rows={3}
            value={form.sellerCopy}
            placeholder="粘贴卖家描述,AI 报告会标注其中可能夸大的话术。"
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
              update("sellerCopy", e.target.value)
            }
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="notes">个人备注(仅自己可见)</Label>
          <Textarea
            id="notes"
            rows={2}
            value={form.notes}
            placeholder="如:朋友拿来寄售,需要 7 天内反馈"
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
              update("notes", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <Label>后续意向</Label>
          <div className="flex flex-wrap gap-3 text-sm">
            {INTENT_OPTIONS.map((opt) => {
              const checked = form.intents.includes(opt);
              return (
                <label key={opt} className="flex cursor-pointer items-center gap-2">
                  <Checkbox
                    checked={checked}
                    onCheckedChange={(v) => toggleIntent(opt, v === true)}
                  />
                  <span>{opt}</span>
                </label>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TextField({
  id,
  label,
  value,
  placeholder,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  placeholder?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
      />
    </div>
  );
}

/* ----- 步骤 5: 生成报告 ----- */
function StepReport({
  tierLabel,
  remainingReports,
  monthlyTokens,
  tokenResetDay,
  generated,
  onGenerate,
}: {
  tierLabel: string;
  remainingReports: number;
  monthlyTokens: number;
  tokenResetDay: number;
  generated: boolean;
  onGenerate: () => void;
}) {
  return (
    <Card className="border-gold-antique/30">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div>
          <CardDescription>第 5 步</CardDescription>
          <CardTitle className="font-serif text-base">生成 AI 报告</CardTitle>
        </div>
        <MockBadge status="mock" label="当前为 Mock 报告" />
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
          <Stat label="当前会员" value={tierLabel} accent />
          <Stat
            label="预计本次消耗"
            value={`~${ESTIMATED_TOKENS.toLocaleString()} Token`}
          />
          <Stat
            label="当月剩余 Token"
            value={`~${monthlyTokens.toLocaleString()}`}
          />
          <Stat label="剩余报告次数" value={`${remainingReports} 次`} />
        </dl>

        <div className="rounded-md bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          Token 配额按月重置(每月 {tokenResetDay} 号)。Mock 阶段不会真正扣减次数;
          真实接入后,生成前会先做配额校验。
        </div>

        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning">
          <FileText className="mr-1 inline h-3.5 w-3.5" aria-hidden />
          AI 模块尚未真实接入,本次报告为内置 Mock 文案,仅用于流程演示。
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            onClick={onGenerate}
            disabled={generated}
            className="cursor-pointer"
          >
            <Sparkles className="mr-1 h-4 w-4" aria-hidden />
            {generated ? "正在跳转到案例..." : "生成报告(Mock)"}
          </Button>
          <Button asChild variant="ghost" className="cursor-pointer">
            <Link href="/cases">
              <Camera className="mr-1 h-4 w-4" aria-hidden />
              查看历史案例
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={`mt-0.5 ${accent ? "text-gold-antique" : "font-medium"}`}>
        {value}
      </dd>
    </div>
  );
}
