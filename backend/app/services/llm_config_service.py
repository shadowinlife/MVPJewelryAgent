"""LLM 配置管理服务 — 管理后台 CRUD + 连通性测试。

职责:
- 从 DB 读取 / 写入 LLM Provider 配置
- API Key 加密存储、脱敏返回
- 连通性测试(发送简单 prompt 验证 Provider 可达)
"""

from __future__ import annotations

import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.llm_provider_config import LLMProviderConfig
from app.integrations.ai.encryption import decrypt_value, encrypt_value, mask_key
from app.schemas.llm_config import LLMConfigRead, LLMConfigTestResult, LLMConfigUpdate

logger = structlog.get_logger(__name__)

# 默认配置键(单行表设计)
_DEFAULT_CONFIG_KEY = "default"


async def get_current_config(session: AsyncSession) -> LLMConfigRead | None:
    """获取当前活跃的 LLM 配置(API Key 脱敏返回)。

    若 DB 无配置,返回 None(调用方应降级到 env vars 或提示用户配置)。
    """
    stmt = select(LLMProviderConfig).where(
        LLMProviderConfig.config_key == _DEFAULT_CONFIG_KEY,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        # 尝试从 env vars 构造默认响应(给前端展示当前状态)
        settings = get_settings()
        if settings.dashscope_api_key:
            return LLMConfigRead(
                provider="dashscope",
                api_key_masked=mask_key(settings.dashscope_api_key),
                endpoint=settings.dashscope_endpoint,
                model_name=settings.dashscope_model,
                is_active=True,
                updated_at=None,
            )
        return None

    # 解密 key 后脱敏
    try:
        plaintext_key = decrypt_value(row.api_key_encrypted)
        masked = mask_key(plaintext_key)
    except Exception:
        masked = "****[解密失败]"

    return LLMConfigRead(
        provider=row.provider,
        api_key_masked=masked,
        endpoint=row.endpoint,
        model_name=row.model_name,
        is_active=row.is_active,
        updated_at=row.updated_at,
    )


async def update_config(
    session: AsyncSession,
    payload: LLMConfigUpdate,
    *,
    admin_id: int | None = None,
) -> LLMConfigRead:
    """创建或更新 LLM 配置。

    若 payload.api_key 为 None,保留 DB 中原有加密值(不修改密钥)。
    """
    stmt = select(LLMProviderConfig).where(
        LLMProviderConfig.config_key == _DEFAULT_CONFIG_KEY,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()

    if row is None:
        # 首次配置 — 必须提供 api_key
        if not payload.api_key:
            msg = "首次配置必须提供 API Key"
            raise ValueError(msg)
        row = LLMProviderConfig(
            config_key=_DEFAULT_CONFIG_KEY,
            provider=payload.provider,
            api_key_encrypted=encrypt_value(payload.api_key),
            endpoint=payload.endpoint,
            model_name=payload.model_name,
            is_active=True,
            updated_by_admin_id=admin_id,
        )
        session.add(row)
    else:
        # 更新现有配置
        row.provider = payload.provider
        row.endpoint = payload.endpoint
        row.model_name = payload.model_name
        row.updated_by_admin_id = admin_id
        if payload.api_key:
            row.api_key_encrypted = encrypt_value(payload.api_key)

    await session.commit()
    await session.refresh(row)

    # 解密后脱敏返回
    plaintext_key = decrypt_value(row.api_key_encrypted)
    return LLMConfigRead(
        provider=row.provider,
        api_key_masked=mask_key(plaintext_key),
        endpoint=row.endpoint,
        model_name=row.model_name,
        is_active=row.is_active,
        updated_at=row.updated_at,
    )


async def test_connection(session: AsyncSession) -> LLMConfigTestResult:
    """测试当前 LLM 配置的连通性 — 发送一条简单 prompt 验证可达。"""
    from app.integrations.ai.factory import get_llm_client

    start = time.perf_counter()
    try:
        client = await get_llm_client(session)
        response = await client.generate(
            messages=[{"role": "user", "content": "Say hello in one word."}],
            max_tokens=10,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("llm_connection_test_ok", latency_ms=latency_ms)
        return LLMConfigTestResult(
            success=True,
            latency_ms=latency_ms,
            model_response=response[:100],
        )
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("llm_connection_test_failed", error=str(e))
        return LLMConfigTestResult(
            success=False,
            latency_ms=latency_ms,
            error=str(e)[:200],
        )
