"""async 数据库 engine 与 sessionmaker 单例。

- `get_engine(settings)` → `AsyncEngine`:进程内单例(通过 `lru_cache`),
  按 `Settings.database_url` + 池参数构造;`pool_pre_ping=True` 防 stale
  connection(阿里云 RDS 默认 idle 8h 后断连)。
- `get_sessionmaker(settings)` → `async_sessionmaker[AsyncSession]`:绑定上
  述 engine;`expire_on_commit=False` 是 async 必备(避免 commit 后属性失
  效需要再 await),`autoflush=False` 让显式 flush 控制时机(对应路由里的
  `async with session.begin()`)。
- `AsyncSessionLocal`:模块级 sessionmaker 单例,`get_db()` 与 `/health.db`
  直接拿;测试覆盖时通过 `app.dependency_overrides` 注入新的 sessionmaker
  即可,无需改本模块。

为什么不用 `async with engine.begin() as conn:` 直接发 SQL:Session 提供
identity map / change tracking,业务路由需要;裸 connection 留给 Alembic
env.py 与 `/health.db` 这种纯 SELECT 1 场景。
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


@lru_cache(maxsize=1)
def _build_engine(
    database_url: str, pool_size: int, max_overflow: int, pool_timeout: int, echo: bool
) -> AsyncEngine:
    """构造 `AsyncEngine` 单例。

    缓存键用各字段标量(不是整个 `Settings`)的原因:`Settings` 是 Pydantic
    模型,不可哈希;而 `lru_cache` 要求参数可哈希。把扁平参数传进来既能缓存,
    又方便测试改单个参数重建 engine。
    """
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True,
        echo=echo,
        future=True,
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """返回进程级 `AsyncEngine` 单例。

    `settings=None` 时走 `get_settings()`,生产/开发主路径;测试可显式传
    自定义 `Settings` 让不同测试拿不同 engine(配合 `_build_engine.cache_clear()`)。
    """
    s = settings or get_settings()
    return _build_engine(
        database_url=str(s.database_url),
        pool_size=s.db_pool_size,
        max_overflow=s.db_max_overflow,
        pool_timeout=s.db_pool_timeout,
        echo=s.db_echo,
    )


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """返回绑定到 engine 单例的 `async_sessionmaker`。

    `expire_on_commit=False`:async 必备 — 默认 True 会在 commit 后把所有 ORM
    属性置为 expired,下次访问触发隐式 refresh,在 async 上下文里会抛
    `MissingGreenlet`。
    `autoflush=False`:不在每次 query 前自动 flush;路由层用 `async with
    session.begin():` 显式管理事务边界,避免 flush 时序混乱。
    """
    engine = get_engine(settings)
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# 模块级 sessionmaker 单例:`get_db` 依赖与 `/health.db` 探活直接使用。
# 测试通过 `app.dependency_overrides[get_db]` 注入自己的 session,
# 不需要替换此变量;路由层一律走 `Depends(get_db)`。
AsyncSessionLocal: async_sessionmaker[AsyncSession] = get_sessionmaker()
