"""信封异常处理回归测试。

覆盖:
- `AppException` → 业务自定义状态码 + 信封;
- `NotFoundError` / `ForbiddenError` 子类 → 各自的 HTTP 状态码;
- 未捕获 `Exception` → 500 + 信封,且响应文案不能泄漏内部细节;
- 失败信封顶层 key 集与前端契约一致(只有 `ok` / `data` / `error` / `source`)。

实现方式:用模块级 autouse fixture 给 *真* FastAPI app 临时挂几个探针路由
(`/__probe/*`),测完即拆,避免污染其它测试文件。
"""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.exceptions import (
    AppException,
    ForbiddenError,
    NotFoundError,
)


@pytest.fixture(scope="module", autouse=True)
def _attach_probe_routes(app: FastAPI) -> Iterator[None]:
    """给 app 挂 4 个故意抛异常的路由,作为本文件用例的 SUT。

    退出 fixture 时主动从 router.routes 删掉,保证测试隔离 — 否则其它
    测试文件可能误调到这些 `/__probe/*` 路由。
    """

    @app.get("/__probe/raises_app_exception")
    async def raises_app_exception() -> None:
        raise AppException("probe.boom", "探针:业务异常", status_code=400)

    @app.get("/__probe/raises_not_found")
    async def raises_not_found() -> None:
        raise NotFoundError(code="case.not_found", message="案例不存在")

    @app.get("/__probe/raises_forbidden")
    async def raises_forbidden() -> None:
        raise ForbiddenError(code="auth.forbidden", message="无权访问")

    @app.get("/__probe/raises_unhandled")
    async def raises_unhandled() -> None:
        raise RuntimeError("explosion")

    yield

    # 清理探针路由;`hasattr(r, "path")` 是为兼容 Starlette 的 Mount / Host 等非 Route 节点。
    app.router.routes = [
        r
        for r in app.router.routes
        if not (hasattr(r, "path") and r.path.startswith("/__probe/"))  # type: ignore[attr-defined]
    ]


@pytest.mark.asyncio
async def test_app_exception_returns_envelope(client: AsyncClient) -> None:
    """业务异常 → 状态码 + 信封;`data` 字段为 null,`error` 是中文短句。"""
    response = await client.get("/__probe/raises_app_exception")
    assert response.status_code == 400

    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"] == "探针:业务异常"
    assert body["source"] == "real"


@pytest.mark.asyncio
async def test_not_found_uses_404(client: AsyncClient) -> None:
    """`NotFoundError` 子类自动用 404 而非默认 400。"""
    response = await client.get("/__probe/raises_not_found")
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "案例不存在"


@pytest.mark.asyncio
async def test_forbidden_uses_403(client: AsyncClient) -> None:
    """`ForbiddenError` 子类自动用 403。"""
    response = await client.get("/__probe/raises_forbidden")
    assert response.status_code == 403
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "无权访问"


@pytest.mark.asyncio
async def test_unhandled_exception_returns_500_envelope(client: AsyncClient) -> None:
    """漏网 `RuntimeError` 兜底为 500 + 信封,且错误文案不能泄漏内部异常类型。"""
    response = await client.get("/__probe/raises_unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body["ok"] is False
    # 一定是友好文案,**不是** "explosion" 或 "RuntimeError"。
    assert body["error"] == "服务器内部错误"
    assert body["source"] == "real"


@pytest.mark.asyncio
async def test_envelope_has_no_extra_keys_on_failure(client: AsyncClient) -> None:
    """失败信封也必须严格等于前端 TS 4 个 key — 没有 `code` / `requestId` / 其它附加字段。"""
    response = await client.get("/__probe/raises_app_exception")
    body = response.json()
    assert set(body.keys()) == {"ok", "data", "error", "source"}
