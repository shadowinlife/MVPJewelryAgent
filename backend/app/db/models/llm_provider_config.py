"""LLM 服务商动态配置模型。

管理员通过后台配置页切换 LLM Provider(DashScope / Azure OpenAI),
无需重新部署即可生效。API Key 在应用层加密后存入 `api_key_encrypted` 字段,
明文永不落盘。

设计为单行表(config_key='default');未来若需按场景路由(report / ocr / embedding)
可扩展为多行,每行一个 config_key。
"""

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class LLMProviderConfig(Base, IdMixin, TimestampMixin):
    """LLM Provider 动态配置(后台可切换,无需重新部署)。"""

    __tablename__ = "llm_provider_configs"

    # 配置键(全局唯一);当前只有 "default",预留按场景扩展。
    config_key: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    # 服务商标识:dashscope | azure_openai
    provider: Mapped[str] = mapped_column(String(30), nullable=False)

    # Fernet 加密后的 API Key(密文存储,应用层解密)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # 服务端点 URL
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)

    # 默认模型名(DashScope: qwen-max; Azure: deployment name)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 启用标记;预留多 Provider 并存时的开关
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # 最后修改的管理员 ID(审计用;外键约束推迟到 Stage 4 auth 落地后加)
    updated_by_admin_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
