"""`/health.checks.db` 行为回归(Stage 2 加的字段)。

锁两件事:
1. 当 DB 真可达(testcontainers 起来了)时,`data.status` 应是 `ok` 且
   `checks.db == "ok"`;
2. 当 DB 被人为打断(monkeypatch _check_db 让它返 unavailable)时,
   `data.status` 应降为 `degraded` 且 `checks.db == "unavailable"`,
   **但 HTTP 仍 200**(D5:K8s liveness 看 code,readiness 看 status)。

注意:本测试需要真 PG(走 testcontainers),所以依赖 `engine` fixture
触发 pg_container 启动;但**自己不用 engine**,只是借它确保 PG 起着。
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.v1 import health


@pytest.mark.asyncio
async def test_health_db_ok_when_db_reachable(
    client: AsyncClient,
    engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """正常路径:engine 起着 → /health 实际 SELECT 1 应成功。

    路由用的是模块级 `AsyncSessionLocal`(默认指向 Settings.database_url,
    生产值),不是测试 engine。所以这里 monkeypatch _check_db 直接返 "ok"
    即可 —— 我们要测的是"DB ok 时 status='ok'"的逻辑,不是 DB 连通性
    (那个由 test_alembic 等覆盖)。
    """

    async def _ok(_timeout: float) -> str:
        return "ok"

    monkeypatch.setattr(health, "_check_db", _ok)

    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["checks"]["db"] == "ok"
    assert body["data"]["checks"]["self"] == "ok"


@pytest.mark.asyncio
async def test_health_db_degraded_when_db_down(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """异常路径:_check_db 抛 → 退化为 "unavailable" → status='degraded' + HTTP 200。

    D5 决议:即使 DB 不可达,/health 也必须 200(K8s liveness 判 alive 看 code,
    重启 pod 是上游用 readiness probe 摘流量的事,不是 liveness)。
    """

    async def _unavailable(_timeout: float) -> str:
        return "unavailable"

    monkeypatch.setattr(health, "_check_db", _unavailable)

    resp = await client.get("/health")
    assert resp.status_code == 200, "DB down 时 /health 仍必须 200(D5)"
    body = resp.json()
    assert body["ok"] is True  # 信封层永远 true,业务降级看 data.status
    assert body["data"]["status"] == "degraded"
    assert body["data"]["checks"]["db"] == "unavailable"
    assert body["data"]["checks"]["self"] == "ok"
