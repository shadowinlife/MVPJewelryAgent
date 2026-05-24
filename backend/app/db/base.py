"""ORM 基类与三个公共 mixin。

严格按 Backend-Database-Schema §6.2 范本落地:
- `Base`:SQLAlchemy 2.0 `DeclarativeBase`,所有 Model 必继承;Alembic 通过
  `Base.metadata` 拿到全部表定义。
- `IdMixin`:统一 `id BIGSERIAL PRIMARY KEY`(Schema §1 原则 2 — 内部 PK,
  对外暴露 `*_no` 避免遍历)。
- `TimestampMixin`:`created_at` / `updated_at`,均 `TIMESTAMPTZ` + 服务端
  默认 `now()`;**`updated_at` 实际更新由 PL/pgSQL 触发器自动完成**(Alembic
  0001_init.py 创建 `set_updated_at()` function + 触发器),不靠应用层。
- `MockableMixin`:`is_mock BOOLEAN`,只挂在 §4 表清单标 ✅ 的 11 张表上
  (`ai_call_logs` / `admin_operation_logs` / `sms_codes` 不挂)。

为什么 mixin 用纯类而非 SQLAlchemy 的 `declared_attr`:Schema §6.2 范本就用纯
mixin,SQLAlchemy 2.0 `Mapped` + `mapped_column` 已支持 mixin 上直接声明字段,
不需要 `declared_attr`。

ORM 红线(Schema §6.4 摘抄,代码评审时回看):
1. 禁止 `lazy='dynamic'` / 隐式懒加载 → async 会炸,预先 `selectinload`
2. 禁止 Model 写业务方法 → 留 `services/` 层
3. 禁止 `default=lambda: datetime.utcnow()` → 用 `server_default=func.now()`
4. 一律显式 `nullable=False` / `nullable=True`,不靠 Python None 推断
5. 禁止 SQLAlchemy `Enum` 类型 → 用 `String` + DB CHECK 约束(Alembic 加)
6. 禁止跨 module 循环 import → relationship 用字符串,真类型走 `TYPE_CHECKING`
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM Model 的根基类。

    保持空 body —— Schema 与字段定义由具体 Model + Mixin 提供,Base 只承担
    `DeclarativeBase` 这一身份(让 SQLAlchemy 知道哪些类是 ORM)。
    """


class IdMixin:
    """统一主键 `id BIGSERIAL PRIMARY KEY`。

    为什么用 BigInteger 而不是 Integer:M4 量级虽小(< 10w 行),但 `ai_call_logs`
    长期累计可能达百万级;预防性用 BIGINT,代价仅占额外 4 字节/行,可忽略。
    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )


class TimestampMixin:
    """`created_at` / `updated_at` 时间戳对。

    两个字段都用 `TIMESTAMPTZ`(timezone-aware),DB 侧用 `now()` 默认,
    确保所有时间戳口径统一为 UTC + offset。

    **重要**:`updated_at` 的真正更新依赖 Alembic 0001_init.py 创建的
    `set_updated_at()` 触发器,**不是**应用层 `onupdate=`;原因见 Schema §6.4 红
    线 3 — `func.now()` 默认值能保证 INSERT 时正确,但 UPDATE 必须 DB 触发器才
    能在所有写入路径(包括手动 SQL、Arq worker、admin 直改)都生效。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class MockableMixin:
    """`is_mock BOOLEAN NOT NULL DEFAULT false`。

    每张挂此 mixin 的业务表都强制带 `is_mock` 标记。管理端默认查询补
    `WHERE is_mock = false`,导出接口除非 `?include_mock=true` 否则物理拒绝
    —— Mock 数据与真数据混在一张表里训练 AI / 跑导出会污染样本。

    **不挂此 mixin 的 3 张表**(无业务态,纯日志/凭证):
    - `ai_call_logs`(AI 调用账单,系统记录)
    - `admin_operation_logs`(管理员操作审计,永久禁删)
    - `sms_codes`(验证码,30 天后硬删)
    """

    is_mock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
