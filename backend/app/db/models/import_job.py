"""ImportJob ORM — `import_jobs` 表(Schema §5.4)。

业务定位:**批量导入**历史 Markdown 案例 / 知识库的作业进度跟踪。
一次导入产生一行,`total_count` / `success_count` / `error_count` 实时
累加,`error_detail_json` 存失败明细(便于 admin 重跑)。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, MockableMixin, TimestampMixin


class ImportJob(Base, IdMixin, TimestampMixin, MockableMixin):
    """批量导入作业进度跟踪。"""

    __tablename__ = "import_jobs"

    # 可选:导入产生的知识文件 ID(导入后挂回去,便于回滚定位)
    file_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_files.id"),
        nullable=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )

    # pending | running | succeeded | partial_failed | failed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # 进度计数
    total_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    error_detail_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    created_by_admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
