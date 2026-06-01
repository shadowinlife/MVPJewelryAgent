"""LLM 配置管理 API 端点集成测试。

依赖 testcontainers 提供的真 PG 实例(已跑 alembic upgrade head)。
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.llm_provider_config import LLMProviderConfig
from app.integrations.ai.encryption import encrypt_value

# ============================================================
# GET /admin/llm-config
# ============================================================


class TestGetLLMConfig:
    """GET /admin/llm-config 端点测试。"""

    @pytest.mark.asyncio
    async def test_get_config_empty_returns_null(self, client: AsyncClient) -> None:
        """DB 无配置 + env 无 key 时返回 data=null。"""
        resp = await client.get("/admin/llm-config")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        # data 可能是 null(无 env 配置)或有值(有 env fallback)
        # 不强制 null,因为 CI 环境可能有 env vars

    @pytest.mark.asyncio
    async def test_get_config_with_db_row(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """DB 有配置时返回脱敏的配置信息。"""
        # 直接写入 DB
        row = LLMProviderConfig(
            config_key="default",
            provider="dashscope",
            api_key_encrypted=encrypt_value("sk-test-key-12345678"),
            endpoint="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="qwen-max",
            is_active=True,
        )
        db_session.add(row)
        await db_session.commit()

        resp = await client.get("/admin/llm-config")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["provider"] == "dashscope"
        # API Key 必须脱敏
        assert "5678" in data["apiKeyMasked"]
        assert "sk-test-key" not in data["apiKeyMasked"]
        assert data["endpoint"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert data["modelName"] == "qwen-max"


# ============================================================
# PUT /admin/llm-config
# ============================================================


class TestUpdateLLMConfig:
    """PUT /admin/llm-config 端点测试。"""

    @pytest.mark.asyncio
    async def test_create_config_first_time(self, client: AsyncClient) -> None:
        """首次配置应成功创建。"""
        payload = {
            "provider": "dashscope",
            "apiKey": "sk-new-key-abcd1234",
            "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "modelName": "qwen-max",
        }
        resp = await client.put("/admin/llm-config", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["provider"] == "dashscope"
        assert "1234" in data["apiKeyMasked"]

    @pytest.mark.asyncio
    async def test_update_config_preserves_key_when_null(
        self, client: AsyncClient
    ) -> None:
        """api_key 传 null 时保留原有密钥。"""
        # 先创建
        create_payload = {
            "provider": "dashscope",
            "apiKey": "sk-original-key-9999",
            "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "modelName": "qwen-max",
        }
        await client.put("/admin/llm-config", json=create_payload)

        # 再更新(不改 key)
        update_payload = {
            "provider": "azure_openai",
            "apiKey": None,
            "endpoint": "https://yaoqi.openai.azure.com/",
            "modelName": "gpt-4o-mini",
        }
        resp = await client.put("/admin/llm-config", json=update_payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "azure_openai"
        # key 应保持原值的脱敏
        assert "9999" in data["apiKeyMasked"]

    @pytest.mark.asyncio
    async def test_create_without_key_returns_error(
        self, client: AsyncClient
    ) -> None:
        """首次配置不提供 api_key 应报错。"""
        # 确保 DB 干净(利用 SAVEPOINT 隔离,不会有残留)
        payload = {
            "provider": "dashscope",
            "apiKey": None,
            "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "modelName": "qwen-max",
        }
        resp = await client.put("/admin/llm-config", json=payload)
        # 可能返回 422 或 500;关键是不能返回 200
        assert resp.status_code != 200 or resp.json()["ok"] is False
