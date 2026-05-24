"""TokenQuota ORM — `token_quotas` 表(Schema §5.1)。

业务定位:**每用户、每自然月一行**的配额账户。会员开通 / 每月 1 号 cron 触发
生成本月配额,AI 调用扣减 `tokens_used`、报告生成扣减 `reports_used`。
管理员可通过 `admin_extra` 临时加量,审计走 admin_operation_logs。

为什么不只用 `users.role` 当配额来源:
- 5 档 tier 的配额规则会随商业策略调整(参考 [yaoqi-membership-tiers]),
  把额度展开成行,历史月份的扣减留痕,便于账单 / 对账;
- 跨月份只看一行,SELECT 简单;月末归零靠定时插新行(老行不动)。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class TokenQuota(Base, IdMixin, MockableMixin):
    """月度 Token / 报告配额账户(每用户每月一行)。"""

    __tablename__ = "token_quotas"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # YYYYMM 整数(202605);CHECK 约束(Alembic 加)限定合法月份
    period_yyyymm: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    tokens_total: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    reports_total: Mapped[int] = mapped_column(Integer, nullable=False)
    reports_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # 管理员临时加量;独立字段方便审计(对账时区分常规配额 vs 加量)
    admin_extra: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    user: Mapped[User] = relationship(back_populates="token_quotas")

    # 用户 × 月份 唯一(避免一个用户同月多份配额)
    __table_args__ = (
        UniqueConstraint("user_id", "period_yyyymm", name="uq_token_quotas_user_period"),
    )
