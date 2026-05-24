"""DB 依赖占位。

Stage 1 不连任何数据源;本文件存在只是为了让其它模块可以提前 `from
app.deps.db import get_db` 而不报 ImportError(将来路由函数会 `Depends(get_db)`,
现在打的是空 wire 防止 Stage 2 一接就要批量改 import)。

Stage 2 替换实现:
1. 引入 `sqlalchemy.ext.asyncio.AsyncSession` + `async_sessionmaker`;
2. 从 `app.db.session` 拿 engine,产出 session;
3. `yield` 后 `commit()` / `rollback()` 收尾;
4. 删除本文件中的 `NotImplementedError` 分支。
"""

from collections.abc import AsyncIterator
from typing import Any


async def get_db() -> AsyncIterator[Any]:
    """`Depends(get_db)` 占位实现。Stage 1 调用会直接抛 NotImplementedError,
    迫使任何提前误用 DB 的代码立刻失败,而不是静默拿到 None 后再炸在 SQL 层。
    """
    raise NotImplementedError("DB session factory wired in Stage 2 (ORM + Alembic).")
    # 下面这行永远跑不到,但保留可以让 mypy 把函数识别为 AsyncIterator 而不是普通 async 函数。
    yield  # pragma: no cover
