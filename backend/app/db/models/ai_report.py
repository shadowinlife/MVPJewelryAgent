"""AIReport ORM — `ai_reports` 表(Schema §5.3)。

业务定位:**AI 鉴定报告**,一个 case 可有多版本(不同 tier 各一份,管理员
复核后再追加)。`report_type` 区分用途:
- `internal_full`:内部全量,所有字段在
- `user_visible`:按 tier 已裁剪,展示给用户
- `customer_simple`:客户简洁版(无价格、风险粗),`customer_simple_markdown`
  独立字段,前端展示时直接拼;严禁前端裁剪
- `admin_reviewed`:管理员人工复核后追加的版本

JSONB 字段分工:
- `output_json`:13 字段(Product-Spec §15.4)的超集,详见
  skills/ai-integration-engineer.md `GeneratedReport`
- `price_fields_json` / `risk_fields_json`:从 `output_json` 派生,
  方便 `crop_report_for_user(tier)` 按字段集裁剪
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.case import Case


class AIReport(Base, IdMixin, TimestampMixin, MockableMixin):
    """AI 鉴定报告(每 case 可多版本)。"""

    __tablename__ = "ai_reports"

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 4 种类型:internal_full | user_visible | customer_simple | admin_reviewed
    report_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    # 元数据
    model_name: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
    # Azure 端 deployment 名(如 aoai-private-report);私调 deployment 时记录
    deployment_name: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # 输入摘要(脱敏后存,供 audit;不存原图)
    input_summary_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # 报告输出
    output_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    full_markdown: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    user_visible_markdown: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    customer_simple_markdown: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 裁剪辅助字段(从 output_json 派生)
    price_fields_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    risk_fields_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # 状态:pending | generating | succeeded | failed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # === pgvector embedding(M4 写入,召回开关默认关)===
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )

    case: Mapped[Case] = relationship(back_populates="reports")

    __table_args__ = (Index("idx_ai_reports_case_latest", "case_id", "report_type", "created_at"),)
