"""数据访问层(ORM + async engine + sessionmaker)。

子模块导出:
- `Base`:DeclarativeBase 基类,所有 ORM Model 继承它;Alembic 通过
  `Base.metadata` 找到全部表(故 `app/db/models/__init__.py` 必须 re-export
  全部 Model,否则 autogenerate 看不到)。
- `IdMixin` / `TimestampMixin` / `MockableMixin`:三个公共字段 mixin,组合使用。
- `get_engine` / `get_sessionmaker` / `AsyncSessionLocal`:async 引擎单例与
  session 工厂;请求级 Session 通过 `app.deps.db.get_db` 拿。

为什么把 Base 放 `db` 包根而不是 `db/base`:`from app.db import Base` 比
`from app.db.base import Base` 短一截,且 Alembic env.py 也是 `from app.db
import Base`。
"""

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin
from app.db.session import AsyncSessionLocal, get_engine, get_sessionmaker

__all__ = [
    "AsyncSessionLocal",
    "Base",
    "IdMixin",
    "MockableMixin",
    "TimestampMixin",
    "get_engine",
    "get_sessionmaker",
]
