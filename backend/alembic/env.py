"""Alembic env.py — async pattern。

按 SQLAlchemy 2.0 + asyncpg 推荐 pattern 实现:`async_engine_from_config` +
`run_sync()` 跑迁移,避免引入 psycopg/psycopg2 同步驱动(决议 D8)。

关键点:
1. `target_metadata = Base.metadata` —— 必须在 import 时让所有 13 个 Model 被
   加载,故先 `from app.db.models import *` 触发 re-export;
2. `compare_type=True` + `compare_server_default=True` —— 防 autogen 漏类型 /
   默认值变更(Schema §7 红线 2);
3. `sqlalchemy.url` 注入两条路径:
   - online 模式:从 `Settings.database_url` 拿(应用与 alembic 同源);
   - offline 模式:从 `-x url=...` 或环境变量 `DATABASE_URL` 拿(CI / docker
     run --rm migrate 场景);
4. 测试用 testcontainers 起的临时 DB:通过 `cfg.set_main_option(
   "sqlalchemy.url", url)` 注入,本模块 `_resolve_url()` 优先用 cfg 里的值。
"""

from __future__ import annotations

import asyncio
import logging
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 关键:import * 触发 13 Model 的注册到 Base.metadata
from app.core.config import get_settings
from app.db import Base
from app.db.models import *  # noqa: F403 — 触发 re-export,Alembic 才能看到全部表

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

target_metadata = Base.metadata


# 这些索引只在 0001_init.py 用 raw SQL 落(部分索引 WHERE 子句 + GIN + ivfflat;
# SQLAlchemy 2.0 的 Index() 对这些组合支持有限,强行落到 ORM `__table_args__`
# 反而要写一堆 `postgresql_where=text(...)` + `postgresql_using="ivfflat"` +
# `postgresql_ops={...}`,可读性更差,且 GIN 表达式索引(`to_tsvector(...)`)
# SQLAlchemy 直接表达不了)。autogen 比较 ORM↔DB 时会把这些识别为"已删除"
# 索引,需要在 include_object 里显式跳过 —— 它们不在 ORM metadata 里,
# 但确实是合法的 schema 一部分,不应该算 drift。
_RAW_SQL_INDEX_NAMES: frozenset[str] = frozenset(
    {
        "idx_users_role",
        "uq_membership_current",
        "idx_cases_status",
        "idx_cases_intents",
        "idx_cases_search",
        "idx_cases_embedding",
        "idx_ai_call_logs_failed",
        "idx_knowledge_embedding",
        "idx_sms_codes_phone_active",
    }
)


def _include_object(
    obj: object, name: str | None, type_: str, reflected: bool, compare_to: object
) -> bool:
    """autogen / `alembic check` 时过滤掉 raw SQL 维护的索引,避免假阳性 drift。

    只跳过 type_=="index" 且名字在白名单里的;其它对象一律保留(尤其表 / 列 /
    外键 / 约束 —— 那些必须按 ORM 走)。
    """
    return not (type_ == "index" and name in _RAW_SQL_INDEX_NAMES)


def _coerce_async_driver(url: str) -> str:
    """统一升级到 asyncpg 驱动(决议 D8:不引入 psycopg/psycopg2)。

    入口可能传 `postgresql://` / `postgresql+psycopg2://` / `postgresql+psycopg://`
    (testcontainers / alembic.ini / 手动注入),env.py 内部恒走 asyncpg。
    已经是 asyncpg 的不变。
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def _resolve_url() -> str:
    """计算本次迁移用的连接串。

    优先级:cfg.get_main_option("sqlalchemy.url")(测试 fixture 注入)
    > Settings.database_url(应用主路径)。返回前统一升级为 asyncpg 驱动。
    """
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = str(get_settings().database_url)
    return _coerce_async_driver(url)


def run_migrations_offline() -> None:
    """offline 模式:不连 DB,只产 SQL(供 DBA review)。

    Schema §7.4 的 `alembic upgrade head --sql > pending.sql` 走这条路径。
    """
    url = _resolve_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """同步迁移函数;在 async connection 的 `run_sync()` 里执行。

    `compare_type=True` + `compare_server_default=True` 让 `alembic check`
    能识别类型 / 默认值漂移,防 ORM 改了但 migration 没跟上。
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    """online 模式 async 实现:用 asyncpg 驱动连真 DB 跑迁移。"""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _resolve_url()

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 一次性脚本不需要连接池
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """online 模式入口:同步外壳,内部跑 async。"""
    asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
