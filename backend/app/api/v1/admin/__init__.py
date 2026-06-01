"""管理后台 API 路由聚合。

当前模块:
- llm_config: LLM 服务商动态配置(GET / PUT / POST test)
"""

from fastapi import APIRouter

from app.api.v1.admin import llm_config

admin_router = APIRouter(prefix="/admin", tags=["admin"])
admin_router.include_router(llm_config.router)
