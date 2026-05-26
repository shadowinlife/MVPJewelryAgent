"""Stage 3 — crop_report_for_user 服务的 8 条 RBAC 红线锁定测试。

本文件是 Stage 3 验收门(M4 milestone §Stage 3):8 条数据红线 +
UI-Spec §17.3 红线全绿。任何一条红线测试失败,Stage 3 不能宣告完成。

红线对应表(Backend-Architecture §10.3 RBAC 数据红线 / UI-Spec §17.3):

| # | 红线 | 测试函数 |
|---|---|---|
| 1 | free 看不到 basic 及以上字段 | test_free_sees_only_free_slot |
| 2 | basic 看不到 pro 及以上字段 | test_basic_sees_basic_but_not_pro |
| 3 | pro 看不到 business 及以上字段 | test_pro_sees_pro_but_not_business |
| 4 | business 看不到 business_pro 字段 | test_business_sees_business_but_not_business_pro |
| 5 | business_pro 看到全 5 个 slot | test_business_pro_sees_all_five_slots |
| 6 | admin 等同 business_pro(envelope 维度)| test_admin_sees_all_five_slots_like_business_pro |
| 7 | customerBrief 不含价格 / 策略 / 渠道字段 | test_customer_brief_excludes_price_strategy_channel |
| 8 | 任何 tier 序列化都不漏 adminNote | test_no_audience_leaks_admin_note_in_envelope |
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.report import (
    CaseReport,
    InternalCustomerBrief,
    InternalReport,
    MembershipTier,
    ReportAudience,
)
from app.services.report_service import (
    TIER_ORDER,
    build_admin_view,
    build_customer_brief,
    crop_report_for_user,
)

# =============================================================================
# 共享 inline fixture(与 test_report_schemas.py 同源,但本文件独立可读)
# =============================================================================

GENERATED_AT = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
CASE_ID = "case-redline-001"


def _make_internal_full() -> InternalReport:
    """"AI 全档输出"的内部模型 —— 13 字段全部齐全 + admin_note + customer_brief。

    所有红线测试都用这一份输入,断言只看"输出 slot 是否为 None"以及
    "序列化 JSON 是否含某 key",输入端不变量化测试更精准。
    """

    return InternalReport(
        material_hint="疑似 A 货翡翠,色阳水头足",
        risk="存在轻微石纹,不影响整体品质",
        need_reinspect=False,
        price_range="¥8,000 – ¥12,000",
        liquidity="主流市场流通性良好",
        recycle_price="¥6,500",
        full_risk=["底色偏灰", "存在 2mm 棉絮"],
        negotiation_strategy="还价空间 15-20%",
        auction_ceiling="¥10,500",
        channel_hint="走二级市场抛货",
        similar_cases=["2024-Q3 类似挂件 ¥9,800 成交"],
        batch_hint="同坑口可批量收 3-5 件",
        admin_note="内部备注:卖家信用 A 级",
        customer_brief=InternalCustomerBrief(
            material_hint="天然翡翠 A 货",
            quality_highlights=["颜色阳绿", "水头充足"],
            main_risks=["有轻微石纹"],
            need_reinspect=False,
            gentle_conclusion="整体品质不错,可放心购买",
        ),
    )


def _crop(audience: ReportAudience) -> CaseReport:
    """简化样板:用全档 internal + 固定 case_id/generated_at 跑一次裁剪。"""

    return crop_report_for_user(
        audience,
        _make_internal_full(),
        case_id=CASE_ID,
        generated_at=GENERATED_AT,
    )


# =============================================================================
# 红线 1-4:每档用户对"高于自身"的 slot 必须为 None
# =============================================================================


def test_free_sees_only_free_slot() -> None:
    """红线 1:free 用户看不到 basic / pro / business / business_pro 任何 slot。

    UI-Spec §10 "会员锁定" + Backend-Architecture §10.3 #2 物理兜底。
    """

    report = _crop("free")
    assert report.free is not None, "free slot 必须始终非空"
    assert report.basic is None
    assert report.pro is None
    assert report.business is None
    assert report.business_pro is None


def test_basic_sees_basic_but_not_pro() -> None:
    """红线 2:basic 用户看到 free + basic,看不到 pro / business / business_pro。"""

    report = _crop("basic")
    assert report.free is not None
    assert report.basic is not None
    assert report.basic.price_range == "¥8,000 – ¥12,000"
    assert report.pro is None
    assert report.business is None
    assert report.business_pro is None


def test_pro_sees_pro_but_not_business() -> None:
    """红线 3:pro 用户看到 free/basic/pro,看不到 business / business_pro。"""

    report = _crop("pro")
    assert report.basic is not None
    assert report.pro is not None
    assert report.pro.recycle_price == "¥6,500"
    assert report.pro.full_risk == ["底色偏灰", "存在 2mm 棉絮"]
    assert report.business is None
    assert report.business_pro is None


def test_business_sees_business_but_not_business_pro() -> None:
    """红线 4:business 用户看到 free/basic/pro/business,看不到 business_pro。"""

    report = _crop("business")
    assert report.pro is not None
    assert report.business is not None
    assert report.business.negotiation_strategy == "还价空间 15-20%"
    assert report.business.auction_ceiling == "¥10,500"
    assert report.business.channel_hint == "走二级市场抛货"
    assert report.business_pro is None


# =============================================================================
# 红线 5-6:business_pro 与 admin 看到全部 5 个 slot
# =============================================================================


def test_business_pro_sees_all_five_slots() -> None:
    """红线 5:business_pro 是用户最高档,5 个 slot 必须全部非空。"""

    report = _crop("business_pro")
    assert report.free is not None
    assert report.basic is not None
    assert report.pro is not None
    assert report.business is not None
    assert report.business_pro is not None
    assert report.business_pro.similar_cases == ["2024-Q3 类似挂件 ¥9,800 成交"]
    assert report.business_pro.batch_hint == "同坑口可批量收 3-5 件"


def test_admin_sees_all_five_slots_like_business_pro() -> None:
    """红线 6:admin audience 在 envelope 维度等同 business_pro(看全 5 slot)。

    注意:adminNote 仍走独立通道(build_admin_view),不进 envelope ——
    见红线 8。
    """

    report = _crop("admin")
    assert report.free is not None
    assert report.basic is not None
    assert report.pro is not None
    assert report.business is not None
    assert report.business_pro is not None


# =============================================================================
# 红线 7:customerBrief 字段集严格白名单
# =============================================================================


def test_customer_brief_excludes_price_strategy_channel() -> None:
    """红线 7:customerBrief 字段集严格等于 5 个白名单 key,任何 tier 都一致。

    UI-Spec §11.2 "不包含" 清单:回收价 / 压价策略 / 法拍上限 /
    渠道判断 / 内部相似案例 / 会员等级 / 管理员备注 —— 通通不能含。
    """

    expected = {
        "materialHint",
        "qualityHighlights",
        "mainRisks",
        "needReinspect",
        "gentleConclusion",
    }
    # 6 个 audience 跑一遍,customerBrief 字段集都必须一致。
    for audience in ("free", "basic", "pro", "business", "business_pro", "admin"):
        report = _crop(audience)  # type: ignore[arg-type]
        brief_dump = report.customer_brief.model_dump(by_alias=True)
        assert set(brief_dump.keys()) == expected, (
            f"audience={audience} 的 customerBrief key 集偏离白名单: "
            f"{set(brief_dump.keys()) - expected}"
        )


# =============================================================================
# 红线 8:任何 audience 的 envelope JSON 都不含 adminNote
# =============================================================================


def test_no_audience_leaks_admin_note_in_envelope() -> None:
    """红线 8:即便 internal.admin_note 非空,序列化 envelope JSON 也绝不含。

    Stage 3 拍板:ReportAdmin 独立 export,**不进 CaseReport**;路由层
    管理后台视图必须显式调 build_admin_view() 才能拿到 adminNote。本
    测试用全字符串扫描:把 "adminNote" 这个字面量从 JSON 输出中剔得
    彻彻底底,即便未来有人不小心给 CaseReport 加 admin slot,本测试
    立刻能拦下。
    """

    audiences: list[ReportAudience] = [
        "free",
        "basic",
        "pro",
        "business",
        "business_pro",
        "admin",
    ]
    for audience in audiences:
        report = _crop(audience)
        envelope_json = report.model_dump_json(by_alias=True)
        assert "adminNote" not in envelope_json, (
            f"audience={audience}: envelope 中泄漏了 adminNote 字段"
        )
        assert "admin_note" not in envelope_json
        # 内部备注内容字符串也不能出现(防"字段名改了但 value 还在"的极端 case)
        assert "内部备注:卖家信用 A 级" not in envelope_json


# =============================================================================
# 附加用例:build_customer_brief / build_admin_view / TIER_ORDER 合理性
# =============================================================================


def test_build_customer_brief_is_independent_entry() -> None:
    """build_customer_brief 单独可用 —— /api/customer-brief/:caseId 路由的复用入口。

    Stage 4 客户简洁版独立路由(任何 tier 看同一份)直接复用此函数,
    不必构造完整 CaseReport。
    """

    brief = build_customer_brief(_make_internal_full())
    assert brief.material_hint == "天然翡翠 A 货"
    assert brief.quality_highlights == ["颜色阳绿", "水头充足"]
    assert brief.main_risks == ["有轻微石纹"]
    assert brief.need_reinspect is False
    assert brief.gentle_conclusion == "整体品质不错,可放心购买"


def test_build_admin_view_returns_admin_note() -> None:
    """build_admin_view 返回 ReportAdmin,内含 adminNote;Stage 4 admin 路由复用入口。"""

    admin = build_admin_view(_make_internal_full())
    assert admin.admin_note == "内部备注:卖家信用 A 级"
    assert admin.model_dump(by_alias=True) == {"adminNote": "内部备注:卖家信用 A 级"}


def test_build_admin_view_handles_missing_note() -> None:
    """internal.admin_note 为 None 时,build_admin_view 兜底返回空字符串。

    路由层若没在调用前判空就直接调本函数,至少不会 ValidationError;
    但合理用法是路由层 `if internal.admin_note: build_admin_view(...)`。
    """

    internal = _make_internal_full()
    internal.admin_note = None
    admin = build_admin_view(internal)
    assert admin.admin_note == ""


def test_tier_order_covers_all_audiences_and_is_strictly_increasing() -> None:
    """TIER_ORDER 必须覆盖 6 个 audience 且严格递增 —— 决定红线 1-6 全部逻辑。

    若有人无意把 admin 的值改成 < business_pro,红线 6 会"成功"但
    实际上 admin 看不到 business_pro slot,埋下静默 bug。本测试是
    TIER_ORDER 自身的不变量守护。
    """

    expected_audiences: set[ReportAudience] = {
        "free",
        "basic",
        "pro",
        "business",
        "business_pro",
        "admin",
    }
    assert set(TIER_ORDER.keys()) == expected_audiences
    values = [TIER_ORDER[a] for a in ("free", "basic", "pro", "business", "business_pro", "admin")]
    assert values == sorted(values), "TIER_ORDER 必须按 audience 顺序严格递增"
    assert len(values) == len(set(values)), "TIER_ORDER 值不能有重复"


def test_unknown_audience_rejected_by_typing() -> None:
    """传入未声明 audience 字面量,Pydantic 在 CaseReport 构造前不报,但 TIER_ORDER 查询会 KeyError。

    这是 Literal 类型在运行时的真实行为:静态类型 mypy 拦,运行时
    依赖 dict 查表 KeyError 兜底。本测试锁死后者(避免有人把
    TIER_ORDER 改成 `.get(..., 0)` 让未知 audience 被当成 free 静默通过)。
    """

    with pytest.raises(KeyError):
        crop_report_for_user(
            "super_admin",  # type: ignore[arg-type]
            _make_internal_full(),
            case_id=CASE_ID,
            generated_at=GENERATED_AT,
        )


def test_membership_tier_excludes_admin() -> None:
    """MembershipTier(用户会员档)与 ReportAudience(报告受众)是两个概念。

    MembershipTier = 5 档用户;ReportAudience = MembershipTier ∪ {"admin"}。
    Stage 4 路由层做 `users.role → MembershipTier` 翻译 +
    `is_admin ? 'admin' : tier` 决定传给 crop 的 audience —— 本测试
    锁死 MembershipTier 不含 "admin",防止两个概念后续被合并失真。
    """

    import typing

    args = typing.get_args(MembershipTier)
    assert "admin" not in args
    assert set(args) == {"free", "basic", "pro", "business", "business_pro"}


# =============================================================================
# 补充:partial InternalReport(AI 只跑了 free 档)裁剪行为
# =============================================================================


def test_business_pro_audience_with_partial_internal_returns_none_slots() -> None:
    """audience 是 business_pro,但 InternalReport 只填了 free 字段 → 高 tier slot 仍为 None。

    覆盖"AI 失败 / 节省 Token 只跑 free 档"的真实场景:即便用户付费了
    business_pro,该次 case 也只下发 free slot —— 前端据此显示"内容
    生成中"而非"已解锁但空"。
    """

    partial = InternalReport(
        material_hint="翡翠",
        risk="低",
        need_reinspect=False,
        # basic / pro / business / business_pro 字段全部默认 None / []
        customer_brief=InternalCustomerBrief(
            material_hint="翡翠",
            quality_highlights=[],
            main_risks=[],
            need_reinspect=False,
            gentle_conclusion="可购",
        ),
    )
    report = crop_report_for_user(
        "business_pro",
        partial,
        case_id="case-partial",
        generated_at=GENERATED_AT,
    )
    assert report.free is not None
    assert report.basic is None
    assert report.pro is None
    assert report.business is None
    assert report.business_pro is None


def test_internal_report_requires_customer_brief() -> None:
    """InternalReport 必须带 customer_brief —— 任何报告都要附客户版。

    若 AI 偶发不返回 customer_brief 字段,本层应在反序列化阶段就
    ValidationError,而非让 build_customer_brief 在下游炸开。
    """

    raw: dict[str, object] = {
        "materialHint": "x",
        "risk": "x",
        "needReinspect": False,
        # 故意不传 customerBrief
    }
    with pytest.raises(ValidationError):
        InternalReport.model_validate(raw)
