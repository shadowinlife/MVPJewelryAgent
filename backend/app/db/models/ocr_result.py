"""OcrResult ORM — `ocr_results` 表(Schema §5.3)。

业务定位:每次 OCR 识别结果一行,允许重跑(同一 file 多行)。
`parsed_json` / `user_corrected_json` 用 JSONB 容纳结构化抽取(证书字段、
票据字段),Schema §1 原则 6 允许 JSONB 用于"半结构化 / OCR 抽取"场景。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin


class OcrResult(Base, IdMixin, TimestampMixin, MockableMixin):
    """OCR 识别结果(每次识别一行)。"""

    __tablename__ = "ocr_results"

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("case_files.id"),
        nullable=False,
    )

    # 3 种 provider:aliyun_ocr | openai_vision | manual
    provider: Mapped[str] = mapped_column(String(30), nullable=False)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSONB 容纳半结构化抽取(证书号 / 鉴定结论 / 票据金额等)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    user_corrected_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    confidence_level: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )

    # pending | running | succeeded | succeeded_low_conf | failed | skipped
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
