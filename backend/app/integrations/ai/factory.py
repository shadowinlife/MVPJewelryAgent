"""LLM 客户端工厂 — 从 DB 配置动态构造对应 Provider 的客户端实例。

优先级:DB 配置 > 环境变量 > 报错。
每次请求新建实例(配置可能随时被 admin 修改);若后续有性能瓶颈,
可加短 TTL 缓存。
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.llm_provider_config import LLMProviderConfig
from app.integrations.ai.azure_openai_client import AzureOpenAILLMClient
from app.integrations.ai.client import LLMClient
from app.integrations.ai.dashscope_client import DashScopeLLMClient
from app.integrations.ai.encryption import decrypt_value

logger = structlog.get_logger(__name__)


async def get_llm_client(session: AsyncSession) -> LLMClient:
    """从 DB 读取当前活跃 LLM 配置,返回对应 Provider 客户端。

    若 DB 无配置,降级读 env vars(DASHSCOPE_* / AOAI_*);
    若 env 也没有,抛 RuntimeError。
    """
    # 尝试从 DB 加载
    stmt = select(LLMProviderConfig).where(
        LLMProviderConfig.config_key == "default",
        LLMProviderConfig.is_active.is_(True),
    )
    row = (await session.execute(stmt)).scalar_one_or_none()

    if row is not None:
        api_key = decrypt_value(row.api_key_encrypted)
        return _build_client(
            provider=row.provider,
            api_key=api_key,
            endpoint=row.endpoint,
            model_name=row.model_name,
        )

    # 降级:从环境变量构建
    settings = get_settings()
    if settings.dashscope_api_key:
        logger.info("llm_factory_fallback_env", provider="dashscope")
        return DashScopeLLMClient(
            api_key=settings.dashscope_api_key,
            endpoint=settings.dashscope_endpoint,
            model_name=settings.dashscope_model,
        )

    msg = (
        "LLM 配置未就绪:DB 无配置且环境变量 DASHSCOPE_API_KEY / AOAI_API_KEY 均为空。"
        "请通过管理后台配置 LLM Provider 或设置对应环境变量。"
    )
    raise RuntimeError(msg)


def _build_client(
    *,
    provider: str,
    api_key: str,
    endpoint: str,
    model_name: str,
) -> LLMClient:
    """根据 provider 标识构造对应适配器实例。"""
    if provider == "dashscope":
        return DashScopeLLMClient(
            api_key=api_key,
            endpoint=endpoint,
            model_name=model_name,
        )
    if provider == "azure_openai":
        return AzureOpenAILLMClient(
            api_key=api_key,
            endpoint=endpoint,
            model_name=model_name,
        )
    msg = f"不支持的 LLM Provider: {provider}"
    raise ValueError(msg)
