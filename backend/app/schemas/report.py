"""Stage 3 — 报告 tier schemas + 服务端字段裁剪契约。

本模块的核心使命:**让"高级报告字段不下发低权限用户"这条红线由 Pydantic
序列化层物理兜底**(UI-Spec §17.3 "高级报告内容不能只靠前端隐藏";
Backend-Architecture §10.3 RBAC 红线 #2)。

设计要点:

1. 每个 tier slot(`ReportFree` / `ReportBasic` / ... / `ReportBusinessPro`)
   是一个 `extra="forbid"` 的独立 Pydantic 模型,字段集就是该 tier **被允许
   看到**的最小白名单。即便 service 层漏 bug 多塞了字段,序列化时
   ValidationError 会立刻抛 —— 这是物理兜底,不是约定。

2. `CaseReport` envelope 与 `web/lib/types/domain.ts :: CaseReport` 1:1
   字段对齐(`tests/test_report_schemas.py` 用 set 等值断言锁死)。

3. `InternalReport` 是后端**唯一持有**的全量超集,对应
   `ai_reports.output_json`(Schema §12 13 字段映射表);`extra="ignore"`
   容忍 AI 输出未知新字段(入口宽容、出口物理裁剪)。

4. `ReportAdmin` 独立 export,**不进 CaseReport**:防止 /api/reports/:id
   路由对低权限用户意外序列化 adminNote;管理后台视图在 Stage 4 路由
   层另行决定如何暴露(`/admin/cases/:id` 加字段 vs `?as=admin` 切视图)。

5. 命名:Python 内部全部 snake_case;Pydantic `alias_generator=to_camel`
   做对外 JSON 的 camelCase 转换 —— 后端代码可读 + 前端契约不漂。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# =============================================================================
# 类型别名
# =============================================================================

# 5 档用户会员等级 — 与 `web/lib/types/domain.ts :: MembershipTier` 字面值严格一致。
# admin 不在此列(admin 是 role 维度而非 tier 维度);裁剪服务的入参用下面
# `ReportAudience = MembershipTier | Literal["admin"]` 扩展。
MembershipTier = Literal["free", "basic", "pro", "business", "business_pro"]

# 报告"受众" — 实际调用 `crop_report_for_user(...)` 的对象;比 MembershipTier
# 多一个 "admin",代表后台预览视图(看到所有 tier 的内容)。
ReportAudience = MembershipTier | Literal["admin"]

# 数据来源 — 与前端 `DataSource` 一致。Stage 1 已在 `envelope.py` 定义过;
# 此处独立再声明一遍是为了让 `report.py` 不必反向 import envelope.py
# (避免 schemas/ 内部模块环依赖,任一文件可独立 import)。
DataSource = Literal["real", "import", "mock"]


# =============================================================================
# 基类:对外严格 / 对内宽容
# =============================================================================


class _ApiModel(BaseModel):
    """对外 API 响应模型基类:strict + camelCase 输出。

    - `extra="forbid"`:任何未声明字段都抛 `ValidationError`,杜绝
      "service 不小心多塞一个字段"导致权限越界。
    - `alias_generator=to_camel`:Python 内部用 snake_case,序列化对前端
      用 camelCase,对齐 `web/lib/types/domain.ts`。
    - `populate_by_name=True`:测试 / service 层既能用 snake_case 也能用
      camelCase 构造实例,不为单元测试强行造 camelCase 字面量。
    """

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )


class _InternalModel(BaseModel):
    """内部全量模型基类:宽容 + camelCase 兼容。

    `extra="ignore"`:容忍 AI 返回的未知字段(模型升级 / 新版 prompt 加字段
    时不至于让整批报告反序列化失败);代价是**绝不能**作为对外响应模型 ——
    出口必须经 `crop_report_for_user(...)` 转换为 `_ApiModel` 子类。
    """

    model_config = ConfigDict(
        extra="ignore",
        alias_generator=to_camel,
        populate_by_name=True,
    )


# =============================================================================
# 5 个用户 tier slot(对外白名单)
# =============================================================================


class ReportFree(_ApiModel):
    """free 用户可见字段(最小集)。

    任何登录用户(以及客户简洁版预览页)都允许看到这三项 —— 它们是
    "温和提示",不暴露价格 / 风险量化 / 渠道。
    """

    material_hint: str
    risk: str
    need_reinspect: bool


class ReportBasic(_ApiModel):
    """basic 用户在 free 之上**追加**的字段。

    注意是**追加**而非继承 —— 前端 `CaseReport.basic` slot 只装 basic 独有
    字段,free 字段在 `CaseReport.free` slot。这样 5 个 slot 之间字段集
    互斥,debug 时能直接看出"这条字段来自哪个 tier"。
    """

    price_range: str
    liquidity: str


class ReportPro(_ApiModel):
    """pro 用户追加字段:回收价 + 详细风险列表。"""

    recycle_price: str
    full_risk: list[str]


class ReportBusiness(_ApiModel):
    """business 用户追加字段:压价策略 + 法拍上限 + 渠道判断。

    这一层开始涉及"商业敏感建议",前端必须保证只对 business 及以上显示;
    后端这层 schema 是物理兜底。
    """

    negotiation_strategy: str
    auction_ceiling: str
    channel_hint: str


class ReportBusinessPro(_ApiModel):
    """business_pro 用户追加字段:相似历史案例 + 批量出价提示。"""

    similar_cases: list[str]
    batch_hint: str


# =============================================================================
# 独立 schemas(不进 CaseReport envelope)
# =============================================================================


class ReportAdmin(_ApiModel):
    """管理员独有字段(adminNote)。

    **故意不进 CaseReport** —— 若进了 envelope,低权限用户路由也会序列化
    `admin=null`,虽然内容空但暴露了"有 admin 字段"这件事本身。Stage 4
    路由层会决定如何暴露(`/admin/cases/:id` 加字段 / `?as=admin` 切视图)。
    """

    admin_note: str


class ReportCustomerBrief(_ApiModel):
    """客户简洁版报告(UI-Spec §11.2)。

    走独立路由 `/api/customer-brief/:caseId`,**任何 tier 的用户都看到完全
    相同的字段集** —— 这是"对客温和版",**不能含**:回收价 / 压价策略 /
    法拍上限 / 渠道判断 / 内部相似案例 / 会员等级 / 管理员备注(见 §11.2
    "不包含"清单)。
    """

    material_hint: str
    quality_highlights: list[str]
    main_risks: list[str]
    need_reinspect: bool
    gentle_conclusion: str


# =============================================================================
# 顶层 envelope
# =============================================================================


class CaseReport(_ApiModel):
    """完整报告响应 envelope — 与前端 `CaseReport` 1:1 对齐。

    字段语义:

    - `free`:始终非空(任何登录用户都能看);
    - `basic / pro / business / business_pro`:**仅当用户 tier ≥ 该 slot**
      且 InternalReport 中对应字段非空时填充,否则为 `None`(JSON 序列化
      为 `null`),前端据此显示"会员锁定卡"(UI-Spec §10);
    - `customer_brief`:始终非空 —— 任何报告都附带客户简洁版,/api/
      customer-brief 路由可直接复用本字段。

    禁止 service 层直接构造嵌套 dict 后塞进 envelope;必须通过
    `crop_report_for_user(...)` 唯一入口,确保 tier slot 的字段白名单
    由 Pydantic 物理守住。
    """

    case_id: str
    source: DataSource = "real"
    generated_at: datetime
    free: ReportFree
    basic: ReportBasic | None = None
    pro: ReportPro | None = None
    business: ReportBusiness | None = None
    business_pro: ReportBusinessPro | None = None
    customer_brief: ReportCustomerBrief


# =============================================================================
# 内部完整模型(对应 ai_reports.output_json)
# =============================================================================


class InternalCustomerBrief(_InternalModel):
    """InternalReport 内嵌的客户简洁版字段集(与对外 `ReportCustomerBrief`
    字段集等价)。

    独立一个内部类型是为了贯彻"内部模型 extra=ignore / 对外模型 extra=
    forbid"的分层规则 —— 反序列化 `ai_reports.output_json` 时容忍多余字段。
    """

    material_hint: str
    quality_highlights: list[str]
    main_risks: list[str]
    need_reinspect: bool
    gentle_conclusion: str


class InternalReport(_InternalModel):
    """完整内部报告 — 后端唯一持有的全量超集。

    对应 `ai_reports.output_json`(Backend-Database-Schema §12 13 字段
    映射表)。**绝不下发任何用户**,必须经 `crop_report_for_user(...)`
    投影到对应 tier slot 后再序列化。

    字段分组(对应 Schema §12 表):

    - free 层(必填,InternalReport 的最小有效条件):
      material_hint / risk / need_reinspect
    - basic 层(可空 —— AI 失败或未跑高 tier 时缺失):
      price_range / liquidity
    - pro 层:recycle_price / full_risk
    - business 层:negotiation_strategy / auction_ceiling / channel_hint
    - business_pro 层:similar_cases / batch_hint
    - admin 独立:admin_note
    - 客户简洁版独立通道:customer_brief
    - 通用兜底:disclaimer(任何报告页都要显示,UI-Spec §17.3;对外暴露
      由 Stage 4 路由决定 —— 当前 envelope 不带,前端硬编码也接受)
    """

    # free 层(必填)
    material_hint: str
    risk: str
    need_reinspect: bool

    # basic 层
    price_range: str | None = None
    liquidity: str | None = None

    # pro 层
    recycle_price: str | None = None
    full_risk: list[str] = Field(default_factory=list)

    # business 层
    negotiation_strategy: str | None = None
    auction_ceiling: str | None = None
    channel_hint: str | None = None

    # business_pro 层
    similar_cases: list[str] = Field(default_factory=list)
    batch_hint: str | None = None

    # admin 独立
    admin_note: str | None = None

    # 客户简洁版(独立通道,必填 —— 任何报告都要有客户版)
    customer_brief: InternalCustomerBrief

    # 通用免责声明(可选;Stage 4 路由决定是否带到响应)
    disclaimer: str | None = None
