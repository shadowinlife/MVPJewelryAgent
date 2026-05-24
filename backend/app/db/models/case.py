"""Case ORM — `cases` 表(Schema §5.2)。

业务定位:**鉴定/估价案例**的核心实体,串联用户、上传文件、OCR、AI 报告、
管理员复核。一个案例的生命周期通过 `status` 状态机推进:

```
draft ──提交──▶ pending ──Arq worker接──▶ analyzing
                                              │
                ┌─────────────────────────────┼────────────┐
                ▼                             ▼            ▼
            analyzed                  pending_recheck   (失败回 pending)
                │
                └──用户/管理员──▶ archived
```

关键字段:
- `case_no`:对外暴露的 ID(`YQ-2026-000123`),格式避免遍历;内部 PK 仍是 `id`;
- `purpose`:案例目的(8 种用途,CHECK 约束);
- `embedding vector(384)`:M4 写入但**默认不召回**(Settings.rag_recall_enabled 控制),
  日后开 RAG 直接用;
- 价格字段全部 `BIGINT cents`(¥1234.56 → 123456),禁止浮点;
- 意向字段(sell/recycle/consignment)布尔,有专门部分索引服务高价值看板。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.ai_report import AIReport
    from app.db.models.case_file import CaseFile
    from app.db.models.user import User


class Case(Base, IdMixin, TimestampMixin, MockableMixin):
    """鉴定 / 估价案例。"""

    __tablename__ = "cases"

    # 对外暴露 ID(YQ-2026-000123),unique;避免暴露自增 PK 被遍历
    case_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(
        String(40), nullable=False
    )
    sub_category: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # 8 种用途:buy/sell/recycle/auction/study/live_select/customer_consult/business_select
    purpose: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    source_channel: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )

    # 状态机:6 个状态(draft → pending → analyzing → analyzed/pending_recheck → archived)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )
    liquidity_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    material_guess: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )
    quality_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # 物理尺寸 / 重量(自由文本,前端解析)
    weight_text: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bead_size: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ring_size: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # 证书
    certificate_org: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )
    certificate_no: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    # === 价格(全部 BIGINT cents,禁止浮点)===
    purchase_price_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    asking_price_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    auction_start_price_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    deal_price_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    expected_price_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    # 文本字段
    seller_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # === 意向(布尔,服务高价值看板的部分索引)===
    sell_intent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    recycle_intent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    consignment_intent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # 数据来源:real | import | mock(import = 历史导入,与 is_mock 正交)
    data_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="real",
        server_default="real",
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # === pgvector embedding(M4 写入,召回开关默认关)===
    # 384 维对齐 sentence-transformers / Azure text-embedding-3-small 的常用维度
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
    embedding_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # === 关系 ===
    user: Mapped[User] = relationship(back_populates="cases", foreign_keys=[user_id])
    files: Mapped[list[CaseFile]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    reports: Mapped[list[AIReport]] = relationship(back_populates="case")

    # 普通索引:btree;部分索引 / GIN / ivfflat 由 Alembic raw SQL 加
    __table_args__ = (Index("idx_cases_user", "user_id", "updated_at"),)
