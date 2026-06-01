"""LLM 配置管理 schemas — 管理后台读/写 LLM 服务商配置。

字段集精简:仅 Provider 选择 + API Key + Endpoint + Model Name。
不含 prompt 管理 / temperature / top_p 等参数(后续需求再扩)。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# 支持的 LLM Provider 标识
LLMProvider = Literal["dashscope", "azure_openai"]


class _ApiModel(BaseModel):
    """对外 API 响应模型基类(同 report.py 约定)。"""

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )


class LLMConfigRead(_ApiModel):
    """GET 响应:返回当前 LLM 配置(API Key 脱敏)。

    API Key 只显示后 4 位(****xxxx),永不以明文返回前端。
    """

    provider: LLMProvider
    api_key_masked: str = Field(description="脱敏 API Key,仅显示后 4 位")
    endpoint: str
    model_name: str
    is_active: bool
    updated_at: datetime | None = None


class LLMConfigUpdate(_ApiModel):
    """PUT 请求体:管理员更新 LLM 配置。

    `api_key` 为 None 时表示不修改密钥(保留 DB 中原有加密值)。
    """

    provider: LLMProvider
    api_key: str | None = Field(
        default=None,
        description="明文 API Key;传 null 表示不更新",
    )
    endpoint: str = Field(min_length=1, max_length=500)
    model_name: str = Field(min_length=1, max_length=100)


class LLMConfigTestResult(_ApiModel):
    """连通性测试结果。"""

    success: bool
    latency_ms: int | None = None
    model_response: str | None = Field(
        default=None,
        description="模型返回的简短响应(验证连通性)",
    )
    error: str | None = None
