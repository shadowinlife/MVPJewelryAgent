import membershipsData from "@/lib/mock/memberships.json";
import type {
  CaseReport,
  MembershipTier,
  MembershipTierDef,
  ReportTier,
} from "@/lib/types/domain";

export const TIER_ORDER: MembershipTier[] = [
  "free",
  "basic",
  "pro",
  "business",
  "business_pro",
];

export const tiers = membershipsData.tiers as MembershipTierDef[];

export function getTierDef(key: MembershipTier): MembershipTierDef {
  const def = tiers.find((t) => t.key === key);
  if (!def) {
    throw new Error(`未知会员等级: ${key}`);
  }
  return def;
}

export function tierLabel(key: MembershipTier): string {
  return getTierDef(key).name;
}

export function tierAtLeast(
  user: MembershipTier,
  required: MembershipTier,
): boolean {
  return TIER_ORDER.indexOf(user) >= TIER_ORDER.indexOf(required);
}

/**
 * 把完整报告按当前会员等级裁剪:
 *  - 把 ≤ user 等级的字段聚合成 `visible`
 *  - 高于 user 等级的字段层(business / businessPro 等)置 null
 *  - 提供 `lockedTiers` 列表给前端渲染 LockedCard
 */
export interface CroppedReport {
  caseId: string;
  source: CaseReport["source"];
  generatedAt: string;
  userTier: MembershipTier;
  visible: ReportTier;
  lockedTiers: MembershipTier[];
}

const TIER_FIELD_MAP: Record<
  MembershipTier,
  keyof Pick<CaseReport, "free" | "basic" | "pro" | "business" | "businessPro">
> = {
  free: "free",
  basic: "basic",
  pro: "pro",
  business: "business",
  business_pro: "businessPro",
};

export function cropReportForUser(
  report: CaseReport,
  userTier: MembershipTier,
): CroppedReport {
  const userIdx = TIER_ORDER.indexOf(userTier);
  const visible: ReportTier = {};
  for (let i = 0; i <= userIdx; i += 1) {
    const tier = TIER_ORDER[i];
    const slice = report[TIER_FIELD_MAP[tier]] as ReportTier | null;
    if (slice) Object.assign(visible, slice);
  }
  const lockedTiers = TIER_ORDER.slice(userIdx + 1);
  return {
    caseId: report.caseId,
    source: report.source,
    generatedAt: report.generatedAt,
    userTier,
    visible,
    lockedTiers,
  };
}

export const tokenPolicy = (membershipsData as {
  tokenPolicy: { basis: string; resetDay: number; note: string };
}).tokenPolicy;

export const lockedCardCopy = (membershipsData as {
  lockedCardCopy: {
    title: string;
    description: string;
    ctaLabel: string;
    helperText: string;
  };
}).lockedCardCopy;
