"""pytest 公共 fixtures。

只放跨多个测试文件共享的 fixture;单文件专属的 fixture(例如 `test_envelope.py`
里挂的探针路由)留在该文件内部,避免本文件膨胀。
"""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app


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
