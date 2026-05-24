"""`/health` 健康探测端点。

Stage 1:只检查"自身存活"(进程能跑 FastAPI 路由)。
Stage 2:扩 `checks.db`(SELECT 1 + 超时);任一第三方挂了把 `data.status`
降为 `"degraded"`,但 HTTP 仍返 200 —— K8s liveness 看 HTTP code(进程活就
不重启),readiness 看 `data.status`(degraded 时摘流量)。
Stage 4 起会再扩 `checks.redis/oss/aoai`。

设计参考:Backend-Architecture §15 验收项 #10。
"""

from __future__ import annotations

import asyncio
from typing import Literal

import structlog
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.envelope import ApiResponse

router = APIRouter(tags=["health"])

logger = structlog.get_logger(__name__)


# 单项检查的状态;阶段细分:
# - "ok":可用
# - "degraded":部分功能可用(例如 OSS 能上传不能列举)
# - "unavailable":完全不可用,需要告警
# - "not_configured":Settings 未配置,本环境刻意不接(例如 local 不接 OSS)
CheckStatus = Literal["ok", "degraded", "unavailable", "not_configured"]


class HealthData(BaseModel):
    """`/health` 响应的 `data` 段。

    `status` 是总体结论(任一第三方挂了就降级);`version` 暴露给前端 / 客户端
    上报 / 监控告警;`checks` 是字典形式给监控系统直接 scrape。
    """

    status: CheckStatus
    version: str
    checks: dict[str, CheckStatus]


async def _check_db(timeout: float) -> CheckStatus:
    """对 Postgres 跑 `SELECT 1` 探活。

    用 `asyncio.timeout` 兜底超时(常见原因:DB 主从切换 / 网络抖动);超时
    或任何异常都标 `unavailable`,**不**抛 —— `/health` 必须保持 HTTP 200。
    """
    try:
        async with asyncio.timeout(timeout):
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        # 不打印连接串(避免 .env 密码漏到日志);只记异常类型与消息开头
        logger.warning("health.db.unavailable", error_type=type(exc).__name__, msg=str(exc)[:200])
        return "unavailable"


def _aggregate_status(checks: dict[str, CheckStatus]) -> CheckStatus:
    """从单项 checks 聚合出 `data.status`。

    规则:任一 `unavailable` → `degraded`(整体降级);任一 `degraded` → `degraded`;
    其余(全 ok 或 not_configured 混 ok)→ `ok`。
    **不返 `unavailable`**:`/health` 总是 HTTP 200,`unavailable` 留给单项 checks
    自身表达,不污染整体。
    """
    for s in checks.values():
        if s in ("unavailable", "degraded"):
            return "degraded"
    return "ok"


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    response_model_exclude_none=False,
)
async def health() -> ApiResponse[HealthData]:
    """探测当前实例是否可服务。返回信封形 `ApiResponse[HealthData]`。

    Stage 2 行为:并发探测 self / db;任一失败把 `status` 降为 `degraded`,
    但 HTTP 仍 200。Stage 4 起会再加 redis / oss / aoai 并发探活。
    """
    settings = get_settings()
    db_status = await _check_db(settings.health_db_timeout_seconds)
    checks: dict[str, CheckStatus] = {"self": "ok", "db": db_status}
    data = HealthData(
        status=_aggregate_status(checks),
        version=settings.app_version,
        checks=checks,
    )
    return ApiResponse[HealthData].success(data=data)
