"""pytest 公共 fixtures。

只放跨多个测试文件共享的 fixture;单文件专属的 fixture(例如 `test_envelope.py`
里挂的探针路由)留在该文件内部,避免本文件膨胀。

Stage 2 新增三个 DB 相关 fixtures:
- `pg_container`(session):起一个 `pgvector/pgvector:pg16` testcontainer,
  与生产 RDS PG16 + pgvector 对齐;**整个 pytest 会话只起一次**,首次拉镜像
  需要 1-2 分钟,后续秒级。
- `engine`(session):basis on `pg_container` 的连接 URL 造 async engine,
  并跑一次 `alembic upgrade head` 把 schema 落到 PG;`NullPool` 避免测试
  连接池泄漏。
- `db_session`(per-test):用 SAVEPOINT + rollback 模式做测试隔离;
  **不**每用例 DROP/CREATE schema,节省 ~100ms × 100 用例 ≈ 10s。
  实现参考 SQLAlchemy 2.0 docs "Joining a Session into an External Transaction"。
"""

import threading
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config
from app.main import app as fastapi_app


def _run_in_thread(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """把同步函数挪到独立线程跑,与主 asyncio loop 隔离。

    背景:alembic env.py 用 `asyncio.run()` 起 async migration runner。
    若直接在 pytest 已有 loop 里调用 `command.upgrade(...)`,会触发
    "asyncio.run() cannot be called from a running event loop"。本辅助
    把它丢到独立线程跑(threading,**不**用 asyncio.to_thread 因为后者
    复用同一 loop),异常透传回主线程。
    """
    err: list[BaseException] = []

    def _runner() -> None:
        try:
            fn(*args, **kwargs)
        except BaseException as e:
            err.append(e)

    t = threading.Thread(target=_runner)
    t.start()
    t.join()
    if err:
        raise err[0]


@pytest.fixture(scope="session")
def app() -> object:
    """FastAPI 实例 fixture。

    session-scoped(整个 pytest 会话只构造一次)以减少启动开销;但代价是
    测试函数对 app 状态的修改会跨用例可见 — 个别测试若要挂临时路由,**必须**
    在 fixture 中自行清理(参见 `test_envelope.py::_attach_probe_routes`)。
    """
    return fastapi_app


@pytest_asyncio.fixture
async def client(app: object) -> AsyncIterator[AsyncClient]:
    """httpx AsyncClient,直接走 ASGITransport(不起真 HTTP server)。

    比起 TestClient(同步)的优点:
    - 真正 async,能测 async 路由的并发行为;
    - 无网络栈开销,测试更快、CI 更稳;
    - `base_url="http://testserver"` 让 cookie / referer 测试有 host 头可参考。
    """
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ============================================================
# Stage 2: DB fixtures(testcontainers + alembic + SAVEPOINT)
# ============================================================


def _wait_for_pg_ready(host: str, port: int, timeout: float = 30.0) -> None:
    """轮询 PG 端口直到 TCP accept(testcontainers 自带的 wait 依赖 psycopg2;
    D8 决议不引入 psycopg2,故自己做 TCP-level 探活)。

    超时 30s 给 pgvector 镜像首次 init 留余量(普通 alpine 一般 < 5s,但
    pgvector 镜像比较大,extension 初始化可能多花几秒)。
    """
    import socket
    import time

    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError as e:
            last_err = e
            time.sleep(0.3)
    raise RuntimeError(f"PG at {host}:{port} not ready after {timeout}s: {last_err}")


@pytest.fixture(scope="session")
def pg_container() -> Iterator[PostgresContainer]:
    """启 `pgvector/pgvector:pg16` 容器(session-scoped,只启一次)。

    用 `pgvector/pgvector:pg16` 而非 `postgres:16-alpine`:前者预装 pgvector
    扩展,与生产 RDS PG16+pgvector 对齐;后者要再 `CREATE EXTENSION vector`
    会缺二进制(脆)。

    首次拉镜像需要 1-2 分钟(README 已注明),后续 docker layer cache 命中
    秒级起。

    `with` 退出后,testcontainers 自动调用 container.stop() 回收资源;
    `_wait_for_pg_ready` 自己做 TCP 探活 —— 不依赖 psycopg2(D8 禁引入)。
    """
    with PostgresContainer("pgvector/pgvector:pg16") as pg:
        _wait_for_pg_ready(pg.get_container_host_ip(), int(pg.get_exposed_port(5432)))
        yield pg


def _to_async_url(sync_url: str) -> str:
    """testcontainers 给的 URL 是 sync 驱动,这里翻译成 asyncpg。

    可能出现的两种 sync 前缀都处理:`postgresql+psycopg2://` / `postgresql://`。
    """
    if sync_url.startswith("postgresql+psycopg2://"):
        return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgresql+psycopg://"):
        return sync_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return sync_url


def _to_sync_url(sync_url: str) -> str:
    """alembic env.py 自带 async-engine,但 alembic.ini 的 sqlalchemy.url 必须
    是无 `+asyncpg` 后缀的 sync 形态(env.py 内部会再升级);此处统一去掉。
    """
    return (
        sync_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgresql+psycopg2://", "postgresql://", 1)
        .replace("postgresql+psycopg://", "postgresql://", 1)
    )


@pytest_asyncio.fixture(scope="session")
async def engine(pg_container: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    """session-scoped async engine + 跑一次 `alembic upgrade head`。

    `NullPool` 关掉连接池:测试用例可能跨 event loop(pytest-asyncio 默认 per-test loop),
    带池的 engine 会把 connection 绑死在某个 loop,跨 loop 复用会报
    "Future attached to a different loop"。

    alembic 这里只跑一次 upgrade(把 13 表 + 扩展 + 触发器 + pgvector 列建好);
    单测之间用 SAVEPOINT 隔离,**不**反复 drop/create。
    """
    async_url = _to_async_url(pg_container.get_connection_url())
    sync_url = _to_sync_url(async_url)

    # 跑 alembic upgrade head:env.py 用 cfg.get_main_option("sqlalchemy.url")
    # 注入 URL 优先于 Settings.database_url(_resolve_url 的逻辑)。
    backend_root = Path(__file__).resolve().parent.parent
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", sync_url)
    _run_in_thread(command.upgrade, cfg, "head")

    eng = create_async_engine(async_url, poolclass=NullPool)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """per-test AsyncSession,基于外层 transaction + SAVEPOINT,函数结束 rollback。

    模式说明(参考 SQLAlchemy docs "Joining a Session into an External Transaction"):
    1. 拿一个 connection,开启外层 transaction(`begin()`);
    2. 创建 Session 绑定到这个 connection(`bind=conn`);
    3. 在外层 transaction 内开 SAVEPOINT(`begin_nested()`);
    4. 通过 `after_transaction_end` event 监听:Session 内部 commit 触发
       SAVEPOINT 结束时,自动重启新 SAVEPOINT —— 这样 ORM 代码即便调用
       `session.commit()` 也只是 release SAVEPOINT,真正的外层 transaction
       永远不会 commit;
    5. 测试函数结束后 `trans.rollback()` 一把回滚所有改动,DB 状态归零。

    好处:不需要每用例 DROP/CREATE schema(慢),也不需要每用例 TRUNCATE
    13 张表(易漏 + 外键顺序坑);代价是测试代码里 commit 是"假"commit。
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            async_session = AsyncSession(
                bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )
            try:
                yield async_session
            finally:
                await async_session.close()
        finally:
            # 不管测试里 commit / rollback 了什么,外层 trans rollback 兜底
            if trans.is_active:
                await trans.rollback()
