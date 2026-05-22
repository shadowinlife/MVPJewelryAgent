export type MembershipTier =
  | "free"
  | "basic"
  | "pro"
  | "business"
  | "business_pro";

export type Risk = "low" | "medium" | "high";

export type CaseStatus =
  | "draft"
  | "pending"
  | "analyzing"
  | "analyzed"
  | "pending_recheck"
  | "archived";

export type DataSource = "real" | "import" | "mock";

export type IntegrationStatus = "real" | "mock" | "pending" | "later";

export interface User {
  id: string;
  phone: string;
  phoneSuffix: string;
  nickname: string;
  membership: MembershipTier;
  membershipExpiresAt: string | null;
  remainingReports: number;
  createdAt: string;
  lastLoginAt: string;
  source: DataSource;
}

export interface CaseSummary {
  materialHint: string;
  liquidity: string;
  needReinspect: boolean;
  membershipFloor: MembershipTier;
}

export interface CaseRecord {
  id: string;
  caseNo: string;
  ownerId: string;
  title: string;
  category: string;
  purpose: "购买" | "出售" | "法拍" | "寄售" | "鉴定";
  risk: Risk;
  status: CaseStatus;
  source: DataSource;
  thumbnail: string;
  summary: CaseSummary;
  createdAt: string;
  updatedAt: string;
}

export interface ReportTier {
  materialHint?: string;
  risk?: string;
  needReinspect?: boolean;
  priceRange?: string;
  liquidity?: string;
  recyclePrice?: string;
  fullRisk?: string[];
  negotiationStrategy?: string;
  auctionCeiling?: string;
  channelHint?: string;
  similarCases?: string[];
  batchHint?: string;
}

export interface CaseReport {
  caseId: string;
  source: DataSource;
  generatedAt: string;
  free: ReportTier;
  basic: ReportTier | null;
  pro: ReportTier | null;
  business: ReportTier | null;
  businessPro: ReportTier | null;
  customerBrief: CustomerBrief;
}

/**
 * 客户简洁版报告(UI-Spec §11)。
 * 这份内容会脱离会员体系直接呈现给客户,所以不能含:
 *   回收价 / 压价策略 / 法拍上限 / 渠道判断 / 内部相似案例 / 会员等级 / 管理员备注。
 * 所有字段都应是已经"对客温和"的措辞。
 */
export interface CustomerBrief {
  materialHint: string;
  qualityHighlights: string[];
  mainRisks: string[];
  needReinspect: boolean;
  gentleConclusion: string;
}

export type OcrConfidence = "high" | "medium" | "low";

export interface OcrField {
  key: string;
  label: string;
  value: string;
  confidence: OcrConfidence;
}

export interface OcrResult {
  caseId: string;
  source: DataSource;
  status:
    | "pending"
    | "running"
    | "succeeded"
    | "succeeded_with_low_confidence"
    | "failed";
  imageRef: string;
  fields: OcrField[];
  rawText: string;
}

export interface MembershipTierDef {
  key: MembershipTier;
  name: string;
  priceHint: string;
  monthlyTokens: number;
  monthlyReportQuota: number;
  visibleFields: string[];
  summary: string;
  quotaHint: string;
}

export interface AdminMetrics {
  totalUsers: number;
  paidMembers: number;
  todayNewCases: number;
  pendingRecheck: number;
  ocrFailures: number;
  aiFailures: number;
  highRiskCases: number;
  mockCaseCount: number;
  realCaseCount: number;
  version: string;
}

export interface IntegrationModule {
  key: string;
  label: string;
  status: IntegrationStatus;
  note: string;
}

export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
  source: DataSource;
}
