"""add password_hash column to users table.

Revision ID: 0003_add_user_password_hash
Revises: 0002_add_llm_provider_config
Create Date: 2026-06-01

MVP 阶段使用账密登录(短信接口暂不可用),给 users 表加 password_hash 列。
nullable=True 因为未来 SMS-only 注册用户不设密码。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_user_password_hash"
down_revision: str = "0002_add_llm_provider_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
