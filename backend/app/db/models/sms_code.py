"""SmsCode ORM — `sms_codes` 表(Schema §5.4)。

业务定位:**短信验证码**(登录 / 绑定 / 重置密码)的临时表。
**安全红线**:
- `code_hash`:**不存明文**,服务端 bcrypt/argon2 哈希后落库
- `expires_at`:过期时间(通常 5 分钟),过期后部分索引自动失效
- `attempts`:错误次数计数(达到阈值后锁定)
- `consumed_at`:消费后标记,部分索引 `WHERE consumed_at IS NULL` 只查活码

**特殊**:
- 不挂 `MockableMixin` —— 验证码不是业务数据
- 只有 `created_at` —— 不改,30 天后整行硬删
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin


class SmsCode(Base, IdMixin):
    """短信验证码(临时表,30 天后硬删)。"""

    __tablename__ = "sms_codes"

    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # 验证码哈希(bcrypt/argon2),**禁止存明文**
    code_hash: Mapped[str] = mapped_column(
        String(128), nullable=False
    )

    # 3 种用途:login | bind | reset
    purpose: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 错误次数(达阈值锁定,防爆破)
    attempts: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 活码部分索引:WHERE consumed_at IS NULL 由 Alembic raw SQL 加
