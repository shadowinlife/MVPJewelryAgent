"""`/health` 健康探测端点。

Stage 1 只检查"自身存活"(进程能跑 FastAPI 路由),用于容器编排
(K8s livenessProbe / SLB 健康检查)判断是否分流到本实例。

Stage 2 起会扩成"自身 + DB + Redis + OSS + AOAI 连通性"五维探测,任一第三方
不可达就把 `data.status` 降级为 `"degraded"` 并把具体故障项标在 `checks` 里。
具体设计见 [Backend-Architecture §15 验收项 #10]。
"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.schemas.envelope import ApiResponse

router = APIRouter(tags=["health"])


# 单项检查的状态;阶段细分:
# - "ok":可用
# - "degraded":部分功能可用(例如 OSS 能上传不能列举)
# - "unavailable":完全不可用,需要告警
# - "not_configured":Settings 未配置,本环境刻意不接(例如 local 不接 OSS)
CheckStatus = Literal["ok", "degraded", "unavailable", "not_configured"]


class HealthChecks(BaseModel):
    """单项探测明细。

    Stage 1 只有 `self_`(用尾下划线避开 Python 保留字);Stage 2 起补
    `db / redis / oss / aoai` 等字段。
    """

    self_: CheckStatus

    # 允许 BaseModel 用别名构造,便于将来字段重命名时不破坏外部反序列化。
    model_config = {"populate_by_name": True}


class HealthData(BaseModel):
    """`/health` 响应的 `data` 段。

    `status` 是总体结论(任一第三方挂了就降级);`version` 暴露给前端 / 客户端
    上报 / 监控告警;`checks` 是字典形式给监控系统直接 scrape。
    """

    status: CheckStatus
    version: str
    checks: dict[str, CheckStatus]


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    response_model_exclude_none=False,
)
async def health() -> ApiResponse[HealthData]:
    """探测当前实例是否可服务。返回信封形 `ApiResponse[HealthData]`。

    Stage 1 行为:进程能进到这一行就返 `status="ok"`,`checks={"self": "ok"}`。
    Stage 2 起会并发探测 DB/Redis/OSS/AOAI,任一失败降级为 `degraded` 并返
    具体 `checks` 字典。
    """
    settings = get_settings()
    data = HealthData(
        status="ok",
        version=settings.app_version,
        checks={"self": "ok"},
    )
    return ApiResponse[HealthData].success(data=data)
