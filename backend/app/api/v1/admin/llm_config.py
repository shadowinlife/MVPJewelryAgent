"""管理后台 — LLM Provider 配置 API。

提供三个端点:
- GET  /admin/llm-config       获取当前配置(API Key 脱敏)
- PUT  /admin/llm-config       更新配置
- POST /admin/llm-config/test  连通性测试

注意:当前阶段 admin 认证中间件尚未实现(Stage 4 auth 落地后补充
`Depends(require_admin)`)。临时无鉴权,仅供内部冒烟测试。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.llm_config import LLMConfigRead, LLMConfigTestResult, LLMConfigUpdate
from app.services import llm_config_service

router = APIRouter(prefix="/llm-config")


@router.get("", response_model=ApiResponse[LLMConfigRead | None])
async def get_llm_config(
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[LLMConfigRead | None]:
    """获取当前 LLM 服务商配置(API Key 脱敏返回)。"""
    config = await llm_config_service.get_current_config(session)
    return ApiResponse[LLMConfigRead | None].success(data=config)


@router.put("", response_model=ApiResponse[LLMConfigRead])
async def update_llm_config(
    payload: LLMConfigUpdate,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[LLMConfigRead]:
    """更新 LLM 服务商配置(Provider / Key / Endpoint / Model）。"""
    config = await llm_config_service.update_config(session, payload)
    return ApiResponse[LLMConfigRead].success(data=config)


@router.post("/test", response_model=ApiResponse[LLMConfigTestResult])
async def test_llm_connection(
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[LLMConfigTestResult]:
    """测试当前 LLM 配置连通性 — 发送简单 prompt 验证 Provider 可达。"""
    result = await llm_config_service.test_connection(session)
    return ApiResponse[LLMConfigTestResult].success(data=result)
