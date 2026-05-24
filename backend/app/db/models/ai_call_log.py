"""AICallLog ORM — `ai_call_logs` 表(Schema §5.3)。

业务定位:每次 AI 调用(LLM / OCR / image_summary)一行,服务两件事:
1. 计费 / 配额扣减(`input_token_count` + `output_token_count` × 单价 = 实际成本)
2. 故障归因(`latency_ms` 跨云延迟,`status='failed'` 触发告警)

**特殊**:这张表**不挂 `MockableMixin`** — 系统日志没有"业务态",纯运维。
保留 6 个月后归档到 `ai_call_logs_archive`(Schema §9.1)。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin


class AICallLog(Base, IdMixin):
    """AI 调用账单 + 故障归因日志。

    **不挂 `MockableMixin` / `TimestampMixin`** — 只需 `created_at`,无业务态
    无需 is_mock,无需 updated_at(日志一旦写入不改)。
    """

    __tablename__ = "ai_call_logs"

    # 可选外键:用户 / 案例可能为空(系统级调用如 cron 测试)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )
    case_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("cases.id"),
        nullable=True,
    )

    # 3 种任务:report_generate | ocr_correct | image_summary
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    model_name: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
    # prompt_version 对齐 ai_reports.prompt_version(同次报告生成串起来)
    prompt_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    input_token_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    output_token_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    cost_estimate_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    # 跨云出口必填,延迟过高触发告警
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # success | failed | timeout
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 只有 created_at(无 updated_at):日志一旦写入不改
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_ai_call_logs_user", "user_id", "created_at"),
        # 失败索引:WHERE status<>'success' 由 Alembic raw SQL 加
    )
