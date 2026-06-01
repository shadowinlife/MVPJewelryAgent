"""AI / LLM 集成子包。

对外暴露:
- `LLMClient` Protocol — 统一调用接口
- `get_llm_client()` — 工厂函数,从 DB 配置动态构造 Provider 客户端
"""

from app.integrations.ai.client import LLMClient as LLMClient
from app.integrations.ai.factory import get_llm_client as get_llm_client

__all__ = ["LLMClient", "get_llm_client"]
