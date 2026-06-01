"""add llm_provider_configs table.

Revision ID: 0002_add_llm_provider_config
Revises: 0001_init
Create Date: 2026-06-01

LLM Provider 动态配置表 — 管理后台切换 DashScope / Azure OpenAI。
单行设计(config_key='default'),CHECK 约束限制 provider 合法值。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_llm_provider_config"
down_revision: str = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 llm_provider_configs 表 + CHECK 约束 + updated_at 触发器。"""

    # --- 表 ---
    op.create_table(
        "llm_provider_configs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("config_key", sa.String(40), unique=True, nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("api_key_encrypted", sa.Text, nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("updated_by_admin_id", sa.BigInteger, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- CHECK 约束:provider 合法值 ---
    op.execute(
        """
        ALTER TABLE llm_provider_configs
        ADD CONSTRAINT ck_llm_provider_configs_provider
        CHECK (provider IN ('dashscope', 'azure_openai'))
        """
    )

    # --- updated_at 触发器(复用 0001 创建的 set_updated_at() 函数)---
    op.execute(
        """
        CREATE TRIGGER trg_llm_provider_configs_updated_at
        BEFORE UPDATE ON llm_provider_configs
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    )


def downgrade() -> None:
    """删除 llm_provider_configs 表(触发器随表一起 drop)。"""
    op.drop_table("llm_provider_configs")
