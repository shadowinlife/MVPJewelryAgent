"""AdminOperationLog ORM — `admin_operation_logs` 表(Schema §5.4)。

业务定位:管理员**敏感操作审计**(查看原图 / 导出案例 / 修改会员 / 加配额
/ 删案例),**永久禁删**(Schema §9.1)。所有管理后台的写操作 / 跨权限读
操作都必须落一行,IP + UA 一起记录便于追溯。

**特殊**:
- 不挂 `MockableMixin` —— 审计日志不分 mock(测试也要记一份,看 admin 是否
  误点;真实环境再过滤)
- 只有 `created_at` —— 日志一旦写入不改
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin


class AdminOperationLog(Base, IdMixin):
    """管理员敏感操作审计日志(永久禁删)。"""

    __tablename__ = "admin_operation_logs"

    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 11 种 action(CHECK 约束限定):
    # view_original_image | export_cases | update_membership | grant_quota |
    # delete_case | review_case | import_knowledge |
    # login_admin | logout_admin | create_admin | disable_user
    action: Mapped[str] = mapped_column(
        String(40), nullable=False
    )

    # 操作对象:type + id(避免每种 action 一张表)
    target_type: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    detail_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # IP / UA:风控 + 异地登录告警依据
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (Index("idx_admin_logs_admin", "admin_id", "created_at"),)
