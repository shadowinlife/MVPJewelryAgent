"""User ORM — `users` 表(Schema §5.1)。

业务定位:**所有人的根**(普通用户、企业用户、管理员都是同一张表的不同 `role`),
登录入口、配额账户、案例归属、管理操作审计全部追溯到 `user_id`。

字段亮点:
- `phone` UNIQUE:目前唯一的登录主键(M4 只做手机号登录);
- `wechat_openid` UNIQUE WHERE NOT NULL:微信登录 P1 才上,M4 留位;
- `role` VARCHAR + CHECK(Alembic 加约束):8 种角色;**禁止**用 Postgres ENUM;
- `status` VARCHAR + CHECK:`active` / `disabled`,软删机制(无物理 DELETE)。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.case import Case
    from app.db.models.membership import Membership
    from app.db.models.token_quota import TokenQuota


class User(Base, IdMixin, TimestampMixin, MockableMixin):
    """系统用户(普通 / 企业 / 管理员统一)。"""

    __tablename__ = "users"

    # 登录主键;唯一,目前 M4 只做手机号登录
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    phone_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 微信登录(P1 才上,M4 留位)
    wechat_openid: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True
    )
    wechat_unionid: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    # 展示信息
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 角色 / 状态(CHECK 由 Alembic 添加,见 0001_init.py)
    # 8 种角色:guest / free_user / member_basic / member_pro /
    #          business / business_pro / admin / super_admin
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free_user",
        server_default="free_user",
    )
    # active | disabled,disabled 后无法登录但保留数据(软删)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    # 最近登录时间(用于风控 / 不活跃账号清理)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 关系(用字符串避免循环 import;真类型走 TYPE_CHECKING)
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Membership.user_id",
    )
    token_quotas: Mapped[list[TokenQuota]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    cases: Mapped[list[Case]] = relationship(
        back_populates="user",
        foreign_keys="Case.user_id",
    )

    # 部分索引(只对 active 用户建)— 服务后台按角色筛选
    __table_args__ = (
        Index(
            "idx_users_role",
            "role",
            postgresql_where="status = 'active'",
        ),
    )
