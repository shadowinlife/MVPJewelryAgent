import type { CaseStatus, Risk } from "@/lib/types/domain";

export const RISK_LABEL: Record<Risk, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

export const RISK_CLASS: Record<Risk, string> = {
  low: "text-[var(--color-success)] bg-[color-mix(in_srgb,var(--color-success)_12%,transparent)] ring-[var(--color-success)]/30",
  medium:
    "text-[var(--color-warning)] bg-[color-mix(in_srgb,var(--color-warning)_14%,transparent)] ring-[var(--color-warning)]/30",
  high: "text-[var(--color-danger)] bg-[color-mix(in_srgb,var(--color-danger)_12%,transparent)] ring-[var(--color-danger)]/30",
};

export const STATUS_LABEL: Record<CaseStatus, string> = {
  draft: "草稿",
  pending: "待处理",
  analyzing: "分析中",
  analyzed: "已分析",
  pending_recheck: "待复检",
  archived: "已归档",
};

export const PURPOSE_OPTIONS = [
  "购买",
  "出售",
  "回收",
  "法拍",
  "学习",
  "直播选品",
  "客户咨询",
  "商业选品",
] as const;

export const CATEGORY_OPTIONS = [
  "翡翠手镯",
  "翡翠吊坠",
  "翡翠戒面",
  "和田玉吊坠",
  "和田玉手镯",
  "和田玉籽料原石",
  "彩宝戒指",
  "钻戒",
  "钻石裸石",
  "珍珠",
  "珊瑚",
  "蜜蜡琥珀",
  "其他",
] as const;

export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${formatDate(iso)} ${String(d.getHours()).padStart(2, "0")}:${String(
    d.getMinutes(),
  ).padStart(2, "0")}`;
}
