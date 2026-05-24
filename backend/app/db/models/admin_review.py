"""AdminReview ORM — `admin_reviews` 表(Schema §5.4)。

业务定位:管理员对 AI 报告的**人工复核**,可触发"补图 / 复检 / 驳回"操作。
一个 case 可有多次复核记录(每次状态变更追加一行),`follow_up_status` 跟踪
后续动作(已联系用户 / 待处理 / 复检完成)。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin


class AdminReview(Base, IdMixin, TimestampMixin, MockableMixin):
    """管理员人工复核记录。"""

    __tablename__ = "admin_reviews"

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 4 种复核结论:approved | needs_more_photos | needs_recheck | rejected
    review_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # 人工判断(可覆盖 AI 输出)
    manual_material_judgment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    manual_price_opinion: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    manual_risk_note: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    follow_up_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
