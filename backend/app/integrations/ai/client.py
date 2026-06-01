"""LLM 抽象客户端协议。

业务代码只依赖本 Protocol,不直接 import openai / dashscope SDK。
层次:api → services → integrations(本层),方向单向,禁止逆向依赖。
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """多 Provider LLM 统一调用接口。

    所有 Provider 适配器必须实现本协议的两个方法:
    - generate: 文本/结构化生成
    - embed: 向量嵌入
    """

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        max_tokens: int = 2000,
    ) -> str:
        """发送消息列表,返回模型生成的文本内容。

        Args:
            messages: OpenAI 格式消息列表 [{"role": "user", "content": "..."}]
            model: 可选覆写模型名;为 None 时使用 Provider 配置的默认模型。
            max_tokens: 最大输出 token 数。

        Returns:
            模型生成的纯文本响应。
        """
        ...

    async def embed(
        self,
        *,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """将文本列表转为向量嵌入。

        Args:
            texts: 待嵌入的文本列表。
            model: 可选覆写 embedding 模型名。

        Returns:
            与 texts 等长的浮点向量列表。
        """
        ...
