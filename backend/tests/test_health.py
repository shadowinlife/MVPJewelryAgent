"""`/health` 端点回归测试。

锁两件事:
1. `/health` 永远返 200 + 信封 ok=true(容器编排依赖这个判断 alive);
2. 信封形状与前端 `web/lib/types/domain.ts :: ApiResponse<T>` 字段集严格一致
   (任一字段名漂移立刻 fail,避免前后端联调时才发现)。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_envelope_ok(client: AsyncClient) -> None:
    """正常路径:200 + ok 信封 + Stage 2 的 checks 至少有 self / db。

    `db` 单项可能是 `ok`(测试启了 PG)或 `unavailable`(纯单元测试无 DB);
    本测试只锁 envelope 形状与 checks 必含 key,**不**锁 db 具体值 —— 那个
    交给 `test_health_db.py` 专门验证。
    """
    response = await client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["error"] is None
    assert body["source"] == "real"

    data = body["data"]
    # 整体 status:`ok` 或 `degraded`,但绝不会是 unavailable / not_configured
    # (聚合规则见 health._aggregate_status)
    assert data["status"] in ("ok", "degraded")
    assert data["version"] == "0.1.0"
    # Stage 2 起 checks 必含 self + db;Stage 4 会再补 redis / oss / aoai
    assert set(data["checks"].keys()) >= {"self", "db"}
    assert data["checks"]["self"] == "ok"


@pytest.mark.asyncio
async def test_health_response_keys_match_frontend_contract(client: AsyncClient) -> None:
    """信封顶层 key 集必须严格等于前端 TS interface 的 4 个字段。

    任一字段漂移(后端多/少一个 key)都会让前端 TS narrowing 失败,
    所以在此用 set 等值断言而不是子集断言。
    """
    response = await client.get("/health")
    body = response.json()
    assert set(body.keys()) == {"ok", "data", "error", "source"}
