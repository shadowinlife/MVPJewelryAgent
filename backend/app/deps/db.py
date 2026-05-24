"""DB 依赖:每请求 AsyncSession 工厂。

`Depends(get_db)` 在 FastAPI 路由里产出一个独立 `AsyncSession`,生命周期与
单次请求绑定:
- 进入路由:打开 session
- 路由正常返回:`commit()` 提交事务
- 路由抛异常:`rollback()` 回滚,再把异常向上抛(交给 envelope 中间件转 500)

为什么不在路由内显式 `async with session.begin():` 而是放在 dep 里:
- 多数路由就是"几条 SELECT / INSERT 然后返回",dep 兜底 commit 减少模板代码;
- 需要细粒度事务的复杂路由,可以在 dep 给的 session 上自己 `session.begin_nested()`
  或 `session.begin()`,但要在最外层显式 commit / rollback 后再 yield 控制权
  给 dep —— dep 的 commit 不会重复(SQLAlchemy 检测已 commit 的事务为 no-op)。

测试覆盖:`app.dependency_overrides[get_db]` 注入一个 yields 测试 session 的
async generator 即可,本模块代码不需要改。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """每请求 `AsyncSession` 工厂。

    `async with AsyncSessionLocal()` 用 sessionmaker 单例造一个 session;`yield`
    后路由开始用它;`yield` 之后的代码在路由返回或抛异常时跑(类似上下文管理器
    的 `__exit__`),`commit` 失败也会触发 `rollback`,确保连接归还前事务有明确
    终态。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
