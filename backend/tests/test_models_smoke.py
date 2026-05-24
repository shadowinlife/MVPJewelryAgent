"""13 张 ORM 的最小冒烟。

目的:**证 schema 在 ORM 视角能用**(insert/select/relationship/CHECK/触发器/
pgvector 写入都跑得通),**不**测业务逻辑(那是 Stage 4 的事)。

测试形态约束:
- 每个用例都用 `db_session`(SAVEPOINT 隔离),不污染彼此;
- 不通过 HTTP/路由,直接对 ORM 操作 —— 缩短失败定位路径(挂了一定是 DDL 或 Model);
- `is_mock` 字段 11 张表挂、3 张不挂(Schema §6.2),用例 `test_is_mock_default_false`
  专门验默认值 False 没漂移到 True;
- pgvector 写入 + 距离查询合一(`test_pgvector_insert_and_distance`),
  防止 ivfflat 索引建错维度。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AIReport,
    Case,
    CaseFile,
    Membership,
    TokenQuota,
    User,
)


async def _make_user(session: AsyncSession, phone: str = "13900000001") -> User:
    """便利:插一个最小 user 并 flush 拿到 PK,后续用例复用。"""
    user = User(phone=phone, role="free_user", status="active")
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_create_user_and_membership(db_session: AsyncSession) -> None:
    """User + Membership 串通:relationship 反查、tier 字段、is_current 默认 True。"""
    user = await _make_user(db_session, phone="13900000010")
    membership = Membership(user_id=user.id, tier="free")
    db_session.add(membership)
    await db_session.flush()

    # selectinload 一次 SQL 把 memberships 捞回
    stmt = select(User).where(User.id == user.id).options(selectinload(User.memberships))
    result = await db_session.execute(stmt)
    fetched = result.scalar_one()
    assert len(fetched.memberships) == 1
    assert fetched.memberships[0].tier == "free"
    assert fetched.memberships[0].is_current is True


@pytest.mark.asyncio
async def test_case_with_files_and_report(db_session: AsyncSession) -> None:
    """Case + 2 CaseFile + 1 AIReport 串通,selectinload 防 N+1。"""
    user = await _make_user(db_session, phone="13900000020")
    case = Case(
        case_no="YQ-2026-000001",
        user_id=user.id,
        title="翡翠手镯估价",
        category="翡翠",
        purpose="sell",
    )
    db_session.add(case)
    await db_session.flush()

    file1 = CaseFile(
        case_id=case.id,
        user_id=user.id,
        file_type="jewelry_natural_light",
        oss_bucket="yaoqi-private",
        oss_key_original="cases/1/main.jpg",
    )
    file2 = CaseFile(
        case_id=case.id,
        user_id=user.id,
        file_type="certificate",
        oss_bucket="yaoqi-private",
        oss_key_original="cases/1/cert.pdf",
    )
    report = AIReport(
        case_id=case.id,
        user_id=user.id,
        report_type="internal_full",
        status="pending",
    )
    db_session.add_all([file1, file2, report])
    await db_session.flush()

    stmt = (
        select(Case)
        .where(Case.id == case.id)
        .options(selectinload(Case.files), selectinload(Case.reports))
    )
    fetched = (await db_session.execute(stmt)).scalar_one()
    assert len(fetched.files) == 2
    assert {f.file_type for f in fetched.files} == {"jewelry_natural_light", "certificate"}
    assert len(fetched.reports) == 1
    assert fetched.reports[0].report_type == "internal_full"


@pytest.mark.asyncio
async def test_unique_constraint_user_phone(db_session: AsyncSession) -> None:
    """`users.phone` UNIQUE:重复手机号必须 IntegrityError。"""
    await _make_user(db_session, phone="13900000030")
    duplicate = User(phone="13900000030", role="free_user", status="active")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_partial_index_membership_current(db_session: AsyncSession) -> None:
    """部分唯一索引 `uq_membership_current WHERE is_current`:
    同一 user 不能有两行 is_current=True。
    """
    user = await _make_user(db_session, phone="13900000040")
    m1 = Membership(user_id=user.id, tier="free", is_current=True)
    db_session.add(m1)
    await db_session.flush()

    m2 = Membership(user_id=user.id, tier="basic", is_current=True)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_check_chk_period_yyyymm(db_session: AsyncSession) -> None:
    """`chk_period_yyyymm` CHECK:月份必须 01-12,202613 应拒。"""
    user = await _make_user(db_session, phone="13900000050")
    bad = TokenQuota(
        user_id=user.id,
        period_yyyymm=202613,  # 13 月 — 非法
        tokens_total=20000,
        reports_total=10,
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_updated_at_trigger_fires(db_session: AsyncSession) -> None:
    """`set_updated_at()` 触发器:UPDATE 后 updated_at 应严格大于原值。

    用 raw SQL 直接 UPDATE 然后再 SELECT,避免 ORM 缓存干扰。
    pg_sleep(0.01) 确保两次 now() 拉开 ≥ 10ms。
    """
    user = await _make_user(db_session, phone="13900000060")
    user_id = user.id

    # 拿 created_at / updated_at 初值;clock_timestamp() 即使在同事务内
    # 也会推进,所以 INSERT 与后续 UPDATE 取到的时间不会同步
    res = await db_session.execute(
        text("SELECT created_at, updated_at FROM users WHERE id = :uid"),
        {"uid": user_id},
    )
    created_at, updated_at_before = res.one()

    # 停顿以拉开时差,再 UPDATE 触发 set_updated_at()
    await db_session.execute(text("SELECT pg_sleep(0.01)"))
    await db_session.execute(
        text("UPDATE users SET nickname = 'changed' WHERE id = :uid"),
        {"uid": user_id},
    )

    res2 = await db_session.execute(
        text("SELECT updated_at FROM users WHERE id = :uid"),
        {"uid": user_id},
    )
    updated_at_after = res2.scalar_one()
    assert (
        updated_at_after > updated_at_before
    ), f"触发器未触发:{updated_at_before} → {updated_at_after}"
    assert updated_at_after > created_at


@pytest.mark.asyncio
async def test_pgvector_insert_and_distance(db_session: AsyncSession) -> None:
    """pgvector 端到端:写 384 维向量 + `<->` 距离查询。

    召回开关默认关(Settings.rag_recall_enabled=False),但**写入**通路必须
    通 —— M4 上线日就在 case 表里堆 embedding,等 Stage 5 开召回。
    """
    user = await _make_user(db_session, phone="13900000070")
    # 简单 384 维向量:全 0.1
    vec = [0.1] * 384
    case = Case(
        case_no="YQ-2026-000002",
        user_id=user.id,
        title="pgvector smoke",
        category="翡翠",
        purpose="sell",
        embedding=vec,
        embedding_model="test/dummy-384",
        embedding_generated_at=datetime.now(UTC),
    )
    db_session.add(case)
    await db_session.flush()

    # 拿回来验维度;再用 <-> 查与自身距离应为 0
    fetched = (await db_session.execute(select(Case).where(Case.id == case.id))).scalar_one()
    assert fetched.embedding is not None
    assert len(list(fetched.embedding)) == 384

    # 用 raw SQL 验距离运算符 `<->`(L2)在 vector 列上能跑
    distance_q = "SELECT embedding <-> CAST(:q AS vector) AS d FROM cases WHERE id = :id"
    # 自身向量做查询,距离应 ≈ 0
    res = await db_session.execute(text(distance_q), {"q": str(vec), "id": case.id})
    distance = res.scalar_one()
    assert distance is not None
    assert float(distance) < 1e-6


@pytest.mark.asyncio
async def test_is_mock_default_false(db_session: AsyncSession) -> None:
    """`is_mock` server_default=False:不显式赋值时,DB 落 False 而非 NULL/True。

    覆盖 11 张挂 MockableMixin 的表中的代表:users / cases(其他表同理)。
    """
    user = await _make_user(db_session, phone="13900000080")
    await db_session.flush()
    # 重新 refresh 把 server_default 拉回来(insert 时没传 is_mock,SA 不会自动回填)
    await db_session.refresh(user)
    assert user.is_mock is False

    case = Case(
        case_no="YQ-2026-000003",
        user_id=user.id,
        title="default check",
        category="翡翠",
        purpose="study",
    )
    db_session.add(case)
    await db_session.flush()
    await db_session.refresh(case)
    assert case.is_mock is False
