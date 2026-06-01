"""API v1 路由聚合。

每个业务模块写在独立文件下(`health.py` / 将来的 `auth.py` / `cases.py` 等),
在本文件中 `include_router` 聚合,再由 `app/main.py` 一次性挂到 FastAPI 实例。

不在这里设 `prefix="/api"` — 是否走 `/api/v1` 前缀由 `app/main.py` 集中决策,
保留未来切版本前缀的灵活性。Stage 1 路由直接挂在 `/`,因为 `/health` 是裸路径
(给容器编排 / SLB 健康探测用,加前缀反而不规范)。
"""

from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1.admin import admin_router

# 主聚合路由;每加一个子模块就在这里 include 一次。
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(admin_router)
