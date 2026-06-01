"""DashScope (通义千问) LLM 客户端 — 通过 OpenAI 兼容接口调用。

DashScope 支持 OpenAI SDK 兼容模式:
  base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model = "qwen-max" / "qwen-plus" / "qwen-turbo" / "qwen-max-latest"

业务代码通过 LLMClient Protocol 调用,不感知底层 SDK 细节。
"""

from __future__ import annotations

import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

# DashScope OpenAI 兼容模式默认端点
DASHSCOPE_DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# DashScope 默认 embedding 模型
DASHSCOPE_DEFAULT_EMBEDDING_MODEL = "text-embedding-v3"


class DashScopeLLMClient:
    """通义千问 DashScope 客户端(OpenAI 兼容模式)。

    使用 openai Python SDK 通过自定义 base_url 调用 DashScope,
    无需引入 dashscope 专用 SDK,保持依赖精简。
    """

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = DASHSCOPE_DEFAULT_ENDPOINT,
        model_name: str = "qwen-max",
    ) -> None:
        """初始化 DashScope 客户端。

        Args:
            api_key: DashScope API Key(sk-xxx 格式)。
            endpoint: 兼容接口地址;默认阿里云公网端点。
            model_name: 默认调用模型名。
        """
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=endpoint,
            timeout=60.0,
        )
        self._default_model = model_name

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        max_tokens: int = 2000,
    ) -> str:
        """发送消息列表,返回模型生成的文本内容。"""
        target_model = model or self._default_model
        logger.debug(
            "dashscope_generate",
            model=target_model,
            message_count=len(messages),
        )
        response = await self._client.chat.completions.create(
            model=target_model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "dashscope_generate_ok",
            model=target_model,
            usage_prompt=response.usage.prompt_tokens if response.usage else 0,
            usage_completion=response.usage.completion_tokens if response.usage else 0,
        )
        return content

    async def embed(
        self,
        *,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """将文本列表转为向量嵌入。"""
        target_model = model or DASHSCOPE_DEFAULT_EMBEDDING_MODEL
        logger.debug("dashscope_embed", model=target_model, text_count=len(texts))
        response = await self._client.embeddings.create(
            model=target_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
