"""Stage 3 — 报告 schema 物理白名单回归测试。

本文件守住"序列化层物理拒绝越权字段"这条 RBAC 红线(UI-Spec §17.3 /
Backend-Architecture §10.3 #2)。如果有任意一条用例红,**绝不允许通过
注释跳过**,必须在 schemas/report.py 或调用方修正:这层守不住,后端
就只是"建议性裁剪"而非物理兜底。

测试范围:

- 5 个 tier slot 各自 `extra="forbid"`,塞错字段抛 ValidationError;
- camelCase 序列化 / snake_case 接收(双向)正常;
- `InternalReport` 容忍未知字段(`extra="ignore"`,AI 升级新字段不炸);
- `CaseReport` envelope 形状与前端 `web/lib/types/domain.ts :: CaseReport`
  字段集严格相等(set 等值断言,前端加字段必须同步加这里)。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.report import (
    CaseReport,
    InternalCustomerBrief,
    InternalReport,
    ReportAdmin,
    ReportBasic,
    ReportCustomerBrief,
    ReportFree,
    ReportPro,
)

# =============================================================================
# fixtures — 用 inline 函数而非 pytest fixture,Stage 3 决定不引 factory 层
# =============================================================================


def _make_internal_full() -> InternalReport:
    """构造一个"AI 全档输出"的 InternalReport,所有 tier 字段齐全。

    本函数是本文件 + test_crop_report.py 的唯一数据源 —— 不抽 conftest
    fixture 是为了让用例自包含,reader 能在单文件内看清"测试输入长什么样"。
    """

    return InternalReport(
        material_hint="疑似 A 货翡翠,色阳水头足",
        risk="存在轻微石纹,不影响整体品质",
        need_reinspect=False,
        price_range="¥8,000 – ¥12,000",
        liquidity="主流市场流通性良好",
        recycle_price="¥6,500",
        full_risk=["底色偏灰", "存在 2mm 棉絮"],
        negotiation_strategy="还价空间 15-20%,以石纹为切入点",
        auction_ceiling="¥10,500",
        channel_hint="建议走二级市场抛货,不走拍卖",
        similar_cases=["2024-Q3 类似挂件 ¥9,800 成交", "2024-Q4 同坑口 ¥11,200"],
        batch_hint="同坑口可批量收 3-5 件",
        admin_note="内部备注:此卖家信用 A 级",
        customer_brief=InternalCustomerBrief(
            material_hint="天然翡翠 A 货",
            quality_highlights=["颜色阳绿", "水头充足"],
            main_risks=["有轻微石纹"],
            need_reinspect=False,
            gentle_conclusion="整体品质不错,可放心购买",
        ),
        disclaimer="本报告仅供参考,不作为交易凭证",
    )


# =============================================================================
# 1. extra=forbid 守住越权字段(每个 tier slot 一个反向测试)
# =============================================================================


def test_report_free_rejects_basic_fields() -> None:
    """ReportFree 不能接收 priceRange / recyclePrice 等高 tier 字段。

    红线 1 物理兜底:即便 service 漏 bug 把 priceRange 塞进 free dict,
    Pydantic 立刻抛 ValidationError 而非默默泄漏。
    """

    with pytest.raises(ValidationError) as exc:
        ReportFree.model_validate(
            {
                "materialHint": "翡翠",
                "risk": "低风险",
                "needReinspect": False,
                "priceRange": "¥8000-12000",  # ← 越权字段
            }
        )
    assert "priceRange" in str(exc.value) or "price_range" in str(exc.value)


def test_report_pro_rejects_business_fields() -> None:
    """ReportPro 不能接收 negotiationStrategy(business 层字段)。"""

    with pytest.raises(ValidationError) as exc:
        ReportPro.model_validate(
            {
                "recyclePrice": "¥6500",
                "fullRisk": ["石纹"],
                "negotiationStrategy": "还价 15%",  # ← 越权字段
            }
        )
    assert "negotiationStrategy" in str(exc.value) or "negotiation_strategy" in str(
        exc.value
    )


def test_report_customer_brief_rejects_price_and_strategy_fields() -> None:
    """ReportCustomerBrief 必须拒绝价格 / 策略 / 渠道字段(UI-Spec §11.2 "不包含"清单)。

    客户简洁版面向终端客户,**任何 tier 都看到同一份**;这里若漏字段
    检查,前端就能在 customer-brief 路由意外读到 recyclePrice 等敏感
    字段,违反 UI-Spec §11.2 "不能含回收价 / 压价策略" 红线。
    """

    base = {
        "materialHint": "翡翠",
        "qualityHighlights": ["颜色好"],
        "mainRisks": ["石纹"],
        "needReinspect": False,
        "gentleConclusion": "可购",
    }
    for forbidden in ("recyclePrice", "negotiationStrategy", "auctionCeiling", "channelHint"):
        with pytest.raises(ValidationError):
            ReportCustomerBrief.model_validate({**base, forbidden: "x"})


# =============================================================================
# 2. camelCase ↔ snake_case 双向兼容
# =============================================================================


def test_report_basic_serializes_to_camel_case() -> None:
    """`model_dump(by_alias=True)` 输出的 JSON key 必须是 camelCase。

    后端 Python 内部用 snake_case,对外用 camelCase —— 这个映射靠
    Pydantic `alias_generator=to_camel`;一旦失效,前端 TS 就拿到
    `price_range` 这种破坏契约的 key。
    """

    basic = ReportBasic(price_range="¥8000-12000", liquidity="好")
    dumped = basic.model_dump(by_alias=True)
    assert set(dumped.keys()) == {"priceRange", "liquidity"}
    assert dumped["priceRange"] == "¥8000-12000"


def test_report_basic_accepts_both_snake_and_camel_input() -> None:
    """构造 Pydantic 实例时,snake_case 和 camelCase 入参都接受。

    `populate_by_name=True` 让单元测试不必为构造一个实例强行写
    camelCase 字面量(`ReportBasic(priceRange=...)` vs
    `ReportBasic(price_range=...)` 都要支持)。
    """

    snake = ReportBasic(price_range="¥1", liquidity="好")
    camel = ReportBasic.model_validate({"priceRange": "¥1", "liquidity": "好"})
    assert snake.model_dump() == camel.model_dump()


# =============================================================================
# 3. InternalReport extra=ignore(入口宽容)
# =============================================================================


def test_internal_report_ignores_unknown_fields() -> None:
    """AI 模型升级后多塞一个未知字段,InternalReport 不应反序列化失败。

    这是"入口宽容、出口严格"分层规则的内部模型一侧 —— 若 AI 输出
    多了 `confidence_score` 字段,本层应静默吸收,而非让整批历史报告
    `ai_reports.output_json` 全部反序列化炸开。
    """

    raw = {
        "materialHint": "翡翠",
        "risk": "低",
        "needReinspect": False,
        "customerBrief": {
            "materialHint": "翡翠",
            "qualityHighlights": [],
            "mainRisks": [],
            "needReinspect": False,
            "gentleConclusion": "可购",
        },
        "confidenceScore": 0.92,  # ← AI 新版本加的未知字段
        "futureField": {"nested": "value"},
    }
    internal = InternalReport.model_validate(raw)
    # 未知字段被静默丢弃,不在 dump 中出现。
    assert "confidenceScore" not in internal.model_dump(by_alias=True)
    assert "futureField" not in internal.model_dump(by_alias=True)


# =============================================================================
# 4. CaseReport envelope 与前端 TS 契约 1:1 锁定
# =============================================================================


def test_case_report_top_level_keys_match_frontend_contract() -> None:
    """CaseReport 顶层 key 集必须严格等于 `web/lib/types/domain.ts :: CaseReport` 9 字段。

    这是契约锁:前端加字段必须同步加 schemas/report.py;后端单方面
    加字段会被本测试立刻拦下。frontend ts 见 web/lib/types/domain.ts:73-83。
    """

    report = CaseReport(
        case_id="case-001",
        generated_at=datetime(2026, 5, 26, tzinfo=UTC),
        free=ReportFree(
            material_hint="翡翠", risk="低", need_reinspect=False
        ),
        customer_brief=ReportCustomerBrief(
            material_hint="翡翠",
            quality_highlights=[],
            main_risks=[],
            need_reinspect=False,
            gentle_conclusion="可购",
        ),
    )
    dumped = report.model_dump(by_alias=True)
    assert set(dumped.keys()) == {
        "caseId",
        "source",
        "generatedAt",
        "free",
        "basic",
        "pro",
        "business",
        "businessPro",
        "customerBrief",
    }


def test_case_report_optional_slots_default_to_none() -> None:
    """basic/pro/business/businessPro 不传时必须默认为 None(序列化为 null)。

    前端依赖 `report.basic === null` 这个判定来显示"会员锁定卡"
    (UI-Spec §10);若默认值变成空字典 `{}`,前端会把空卡当成"已解锁
    但内容为空",误导用户。
    """

    report = CaseReport(
        case_id="case-002",
        generated_at=datetime(2026, 5, 26, tzinfo=UTC),
        free=ReportFree(material_hint="x", risk="x", need_reinspect=False),
        customer_brief=ReportCustomerBrief(
            material_hint="x",
            quality_highlights=[],
            main_risks=[],
            need_reinspect=False,
            gentle_conclusion="x",
        ),
    )
    dumped = report.model_dump(by_alias=True)
    assert dumped["basic"] is None
    assert dumped["pro"] is None
    assert dumped["business"] is None
    assert dumped["businessPro"] is None


def test_case_report_rejects_admin_field_in_envelope() -> None:
    """CaseReport envelope 内**不允许出现** admin / adminNote / adminView 字段。

    Stage 3 拍板:ReportAdmin 走独立 export,不进 CaseReport。本测试
    确保即便有人手动 model_validate 一份带 admin key 的 dict 进来,
    Pydantic 也立刻拒绝(extra=forbid 守住)。
    """

    payload: dict[str, object] = {
        "caseId": "case-003",
        "source": "real",
        "generatedAt": "2026-05-26T00:00:00+00:00",
        "free": {"materialHint": "x", "risk": "x", "needReinspect": False},
        "basic": None,
        "pro": None,
        "business": None,
        "businessPro": None,
        "customerBrief": {
            "materialHint": "x",
            "qualityHighlights": [],
            "mainRisks": [],
            "needReinspect": False,
            "gentleConclusion": "x",
        },
        "adminNote": "应被拒绝",  # ← 不应能进 envelope
    }
    with pytest.raises(ValidationError):
        CaseReport.model_validate(payload)


# =============================================================================
# 5. ReportAdmin 独立可用(由 Stage 4 admin 路由复用)
# =============================================================================


def test_report_admin_is_independent_schema() -> None:
    """ReportAdmin 自身可独立构造 / 序列化,字段集只含 adminNote。"""

    admin = ReportAdmin(admin_note="卖家信用 A 级")
    assert admin.model_dump(by_alias=True) == {"adminNote": "卖家信用 A 级"}


# =============================================================================
# 6. 构造 fixture 自检 —— 避免本文件其它用例与 _make_internal_full 漂移
# =============================================================================


def test_internal_full_fixture_has_all_tier_fields() -> None:
    """元测试:_make_internal_full() 必须填齐所有 tier 字段。

    Stage 3 + Stage 4 多个测试文件依赖它"全档"的语义;若有人无意改了
    它只填部分字段,会让 test_crop_report.py 的红线断言失效。
    """

    internal = _make_internal_full()
    assert internal.price_range is not None
    assert internal.liquidity is not None
    assert internal.recycle_price is not None
    assert internal.full_risk
    assert internal.negotiation_strategy is not None
    assert internal.auction_ceiling is not None
    assert internal.channel_hint is not None
    assert internal.similar_cases
    assert internal.batch_hint is not None
    assert internal.admin_note is not None
