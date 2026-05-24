"""KnowledgeFile ORM — `knowledge_files` 表(Schema §5.4)。

业务定位:**RAG 知识库**主源 —— 个人案例库、市场观察、拍卖规则、GB 证书 SOP、
直播话术等。`embedding vector(384)` 用于 RAG 召回(`enabled=true` 才进召回池),
M4 写入但召回开关默认关。
"""

from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin


class KnowledgeFile(Base, IdMixin, TimestampMixin, MockableMixin):
    """知识库文件(RAG 召回主源)。"""

    __tablename__ = "knowledge_files"

    title: Mapped[str] = mapped_column(
        String(160), nullable=False
    )

    # 6 种类型:personal_case | market_observation | auction_rule |
    #         gb_certificate_sop | live_sales_script | other
    file_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )

    oss_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 解析状态:pending | parsing | parsed | failed
    parsed_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # 解析后的摘要;召回 top-k 后参与 prompt(本身不放原文)
    content_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 是否参与召回;ivfflat 部分索引带 WHERE enabled
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    uploaded_by_admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # === pgvector embedding ===
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
