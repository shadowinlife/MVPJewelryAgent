"""Membership ORM — `memberships` 表(Schema §5.1)。

业务定位:用户会员等级**变更历史**表。**不是**用户当前等级的"覆盖"表,
每次升降级 / 续费 / 管理员授予都插一行新记录,旧记录 `is_current=false`。
"当前会员"通过部分唯一索引 `uq_membership_current WHERE is_current` 保证
"用户有且仅有 1 行 `is_current=true`"。

5 个 tier(对应 [yaoqi-membership-tiers memory] 与 web/lib/mock/memberships.json):
free / basic / pro / business / business_pro,核心差异是月度 Token 配额
(2 万 → 200 万),配额具体值在 `token_quotas` 表按月生成。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Membership(Base, IdMixin, MockableMixin):
    """会员等级变更记录(每次变动一行,is_current 标当前生效)。"""

    __tablename__ = "memberships"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 5 档:free | basic | pro | business | business_pro(CHECK 由 Alembic 加)
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 管理员授予会员时记录授权人(自引用 users.id),`grant_reason` 写文本理由
    granted_by_admin_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )
    grant_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 当前生效标记;部分唯一索引保证每个用户只有 1 行 True
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # 注意:这张表只有 created_at,没有 updated_at —— 历史记录原则上不改
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    user: Mapped[User] = relationship(
        back_populates="memberships",
        foreign_keys=[user_id],
    )

    # 部分唯一索引:WHERE 子句用 raw SQL,Alembic 0001_init.py 落
    # 这里只挂普通组合索引;部分唯一索引在 migration 用 op.execute 加
    __table_args__ = (Index("idx_memberships_user", "user_id"),)
