"""Stage 3 — 报告字段裁剪服务(crop_report_for_user 唯一入口)。

本模块解决一条 RBAC 红线:**"高级报告字段(回收价 / 压价策略 / 法拍上限 /
相似案例 / 管理员备注)只能下发给对应 tier 及以上的用户"**(Backend-
Architecture §10.3 RBAC 红线 #2;UI-Spec §17.3 "高级报告内容不能只靠
前端隐藏")。

设计要点(决定为什么是"服务"而不是"工具函数"):

1. **唯一入口约束**:Stage 4 所有报告类路由(`/api/reports/:id` /
   `/api/customer-brief/:caseId` / `/api/admin/cases/:id`)都必须经由本
   模块的 3 个函数构造响应,不准在路由里手搓 dict —— 这是"裁剪只能发生
   一次"的纪律。
2. **物理兜底,不是约定**:`CaseReport` envelope 内 5 个 tier slot 是
   `extra="forbid"` 的独立 Pydantic 模型,即便本 service 漏 bug 多塞了
   字段,Pydantic 序列化层会立刻抛 `ValidationError` 而非默默泄漏。
   `tests/test_crop_report.py` 用 8 条红线断言锁死。
3. **TIER_ORDER 是排序而非字符串比较**:`"basic" > "free"` 字符串顺序
   恰好对,但 `"business_pro" < "free"` 字符串顺序就反了。用显式
   `Mapping[Audience, int]` 让 mypy 看得见、reviewer 一眼能改顺序。
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Final

from app.schemas.report import (
    CaseReport,
    DataSource,
    InternalReport,
    ReportAdmin,
    ReportAudience,
    ReportBasic,
    ReportBusiness,
    ReportBusinessPro,
    ReportCustomerBrief,
    ReportFree,
    ReportPro,
)

# =============================================================================
# tier 排序表 — 决定"≥ 该 tier 才能看到对应 slot"的全部判定
# =============================================================================

# `admin` 视为 business_pro 的真超集(在数值上更大):管理员预览视图能
# 看到所有 5 个用户 slot 的字段(adminNote 仍走独立通道,不进 envelope)。
# Final + Mapping 让本表在模块导入后不可被覆盖,杜绝运行时被偷偷修改
# 顺序的"远端炸弹"。
TIER_ORDER: Final[Mapping[ReportAudience, int]] = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "business": 3,
    "business_pro": 4,
    "admin": 5,
}


# =============================================================================
# 内部 helper(不导出)
# =============================================================================


def _can_view(audience: ReportAudience, required: ReportAudience) -> bool:
    """audience 是否有权访问 ≥ required tier 的字段。

    单独抽函数是为了让裁剪逻辑读起来像业务语句而不是数字比较 ——
    `if _can_view(audience, "pro")` 比 `if TIER_ORDER[audience] >= 2`
    更接近"是否能看 pro 字段"这个业务意图。
    """

    return TIER_ORDER[audience] >= TIER_ORDER[required]


def _build_free(internal: InternalReport) -> ReportFree:
    """构造 free slot — 任何登录用户都能看到的最小集。

    free 层在 `InternalReport` 中是 required 字段(material_hint / risk /
    need_reinspect),所以这里直接读取,不做 None 兜底 —— 若 internal
    在反序列化时缺这三项,早就 `ValidationError` 了,根本进不来本函数。
    """

    return ReportFree(
        material_hint=internal.material_hint,
        risk=internal.risk,
        need_reinspect=internal.need_reinspect,
    )


def _build_basic(internal: InternalReport) -> ReportBasic | None:
    """构造 basic slot — 仅当 InternalReport 中 basic 层字段全部非空时返回。

    返回 `None` 的 case:AI 跑失败 / 该次推理只跑了 free 档(节省 Token)/
    数据未补齐。前端拿到 `null` 后显示"会员锁定卡"或"内容生成中"。
    """

    if internal.price_range is None or internal.liquidity is None:
        return None
    return ReportBasic(
        price_range=internal.price_range,
        liquidity=internal.liquidity,
    )


def _build_pro(internal: InternalReport) -> ReportPro | None:
    """构造 pro slot — full_risk 是 list,空 list 也算"未生成"。

    `full_risk` 默认值是 `[]`(`Field(default_factory=list)`),空列表
    与"业务上 AI 真的判定无风险"两种语义在 Stage 3 这里取严格判定:
    空列表 = 未生成 → 不下发 pro slot。Stage 4 接 AI 实际输出时若需要
    区分,可在 InternalReport 加 sentinel(如 `pro_generated: bool`)。
    """

    if internal.recycle_price is None or not internal.full_risk:
        return None
    return ReportPro(
        recycle_price=internal.recycle_price,
        full_risk=internal.full_risk,
    )


def _build_business(internal: InternalReport) -> ReportBusiness | None:
    """构造 business slot — 三个字段缺一不返回。

    business 层涉及"商业敏感建议"(压价 / 法拍 / 渠道),与其残缺下发
    一条字段不如整 slot 不下发,前端逻辑也更简单(只判 slot 是否 null)。
    """

    if (
        internal.negotiation_strategy is None
        or internal.auction_ceiling is None
        or internal.channel_hint is None
    ):
        return None
    return ReportBusiness(
        negotiation_strategy=internal.negotiation_strategy,
        auction_ceiling=internal.auction_ceiling,
        channel_hint=internal.channel_hint,
    )


def _build_business_pro(internal: InternalReport) -> ReportBusinessPro | None:
    """构造 business_pro slot — similar_cases 与 batch_hint 都要齐全。"""

    if not internal.similar_cases or internal.batch_hint is None:
        return None
    return ReportBusinessPro(
        similar_cases=internal.similar_cases,
        batch_hint=internal.batch_hint,
    )


# =============================================================================
# 公开 API — 3 个入口
# =============================================================================


def crop_report_for_user(
    audience: ReportAudience,
    internal: InternalReport,
    *,
    case_id: str,
    generated_at: datetime,
    source: DataSource = "real",
) -> CaseReport:
    """按 audience tier 裁剪 InternalReport,返回前端可直接序列化的 CaseReport。

    裁剪策略(由 `TIER_ORDER` 严格控制):

    - `free` slot:始终非空(audience ≥ free,而 free 是最低档)。
    - `basic` / `pro` / `business` / `business_pro` slot:audience ≥ 对应
      tier **且** InternalReport 对应字段全部齐全时填充,否则 None。
    - `customerBrief`:**所有 audience 都填充**(包括 free)—— 客户简洁版
      是"对客温和摘要",不分会员等级(UI-Spec §11.2)。
    - `adminNote`:**永不出现在 CaseReport** —— ReportAdmin 走独立通道
      `build_admin_view()`,由 Stage 4 admin 路由单独下发。

    禁止在路由层手搓 dict 后跳过本函数;Pydantic `extra="forbid"` 是最
    后兜底但不是第一道防线,纪律先于工具。
    """

    free = _build_free(internal)

    basic = _build_basic(internal) if _can_view(audience, "basic") else None
    pro = _build_pro(internal) if _can_view(audience, "pro") else None
    business = (
        _build_business(internal) if _can_view(audience, "business") else None
    )
    business_pro = (
        _build_business_pro(internal)
        if _can_view(audience, "business_pro")
        else None
    )

    customer_brief = build_customer_brief(internal)

    return CaseReport(
        case_id=case_id,
        source=source,
        generated_at=generated_at,
        free=free,
        basic=basic,
        pro=pro,
        business=business,
        business_pro=business_pro,
        customer_brief=customer_brief,
    )


def build_customer_brief(internal: InternalReport) -> ReportCustomerBrief:
    """从 InternalReport 抽出客户简洁版字段集(5 字段白名单)。

    单独抽函数有两个用途:

    1. `/api/customer-brief/:caseId` 路由(Stage 4)可以**不构造完整 CaseReport**
       就直接拿到客户版数据 —— 节省一次完整 envelope 构造开销。
    2. 让 `extra="forbid"` 的 `ReportCustomerBrief` 在序列化时物理拒绝任何
       价格 / 策略 / 渠道字段 —— UI-Spec §11.2 "不包含"清单的最后兜底。

    InternalReport 的 `customer_brief: InternalCustomerBrief` 字段在反
    序列化时已经强制 5 字段必填,这里直接 by-name 透传即可。
    """

    inner = internal.customer_brief
    return ReportCustomerBrief(
        material_hint=inner.material_hint,
        quality_highlights=inner.quality_highlights,
        main_risks=inner.main_risks,
        need_reinspect=inner.need_reinspect,
        gentle_conclusion=inner.gentle_conclusion,
    )


def build_admin_view(internal: InternalReport) -> ReportAdmin:
    """从 InternalReport 抽出管理员独有字段(adminNote)。

    走独立通道而非 `CaseReport.admin` slot,理由:

    - **杜绝低权限路由意外序列化**:即便 `/api/reports/:id` 路由忘了过
      `crop_report_for_user`,也不会把 `admin: null` 字段名暴露给用户
      端(暴露"存在 admin 字段"本身就是泄漏)。
    - **路由层显式调用**:Stage 4 写 `/api/admin/cases/:id` 时必须显式
      `admin_view = build_admin_view(internal); ApiResponse(admin=admin_view)`,
      把"是否暴露 adminNote"这个决定明确写在路由代码里,grep 一搜即知。

    `admin_note` 字段在 InternalReport 中是 `str | None`,若 AI 未生成
    管理员备注,这里返回空字符串 —— 上层应在调用前判断是否要构造本
    视图,而不是依赖本函数的 None 兜底。
    """

    return ReportAdmin(admin_note=internal.admin_note or "")
