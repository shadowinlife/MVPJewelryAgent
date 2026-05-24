"""Request ID 中间件回归测试。

锁三件事:
1. 上游传 `X-Request-ID` → 后端原样回写(不丢、不改);
2. 上游没传 → 后端生成 UUID hex(32 位无横线)并回写;
3. 同一 client 连续请求 → 拿到的 ID 各不相同(防止有人误用 contextvar 引入串号)。
"""

import re

import pytest
from httpx import AsyncClient

# UUID hex 是 32 位小写十六进制字符;`request_id.py` 用 `uuid.uuid4().hex` 生成。
UUID_HEX_RE = re.compile(r"^[0-9a-f]{32}$")


@pytest.mark.asyncio
async def test_request_id_passthrough(client: AsyncClient) -> None:
    """请求带 `X-Request-ID` → 响应 header 原值回写。"""
    incoming = "test-request-id-abc-123"
    response = await client.get("/health", headers={"X-Request-ID": incoming})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == incoming


@pytest.mark.asyncio
async def test_request_id_generated_if_absent(client: AsyncClient) -> None:
    """没传 header → 后端生成,且必须符合 UUID hex 格式。"""
    response = await client.get("/health")
    assert response.status_code == 200
    rid = response.headers.get("X-Request-ID")
    assert rid is not None
    assert UUID_HEX_RE.match(rid), f"expected uuid hex, got {rid}"


@pytest.mark.asyncio
async def test_request_id_unique_per_request(client: AsyncClient) -> None:
    """两次独立请求 → 拿到的 ID 必须不同(防 contextvar 串号回归)。"""
    r1 = await client.get("/health")
    r2 = await client.get("/health")
    assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]
