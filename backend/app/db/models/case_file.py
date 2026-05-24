"""CaseFile ORM — `case_files` 表(Schema §5.2)。

业务定位:**案例附件**(图片 / 证书扫描件 / 票据)。文件**不进 DB**,只存
OSS 对象键(`oss_key_*`),原图永久私有,只对登录人按 tier 暴露不同版本:
- `oss_key_original`:原图,内部 / admin 才能拿
- `oss_key_preview`:压缩缩略图,展示用
- `oss_key_watermarked`:水印版,客户简洁版分享用

**安全红线**(Backend-Security-Checklist):Bucket 必须私有,客户简洁版**禁**
public URL;所有访问走 STS 预签名,过期时间 ≤ 300s。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, MockableMixin

if TYPE_CHECKING:
    from app.db.models.case import Case


class CaseFile(Base, IdMixin, MockableMixin):
    """案例附件(图片 / 证书 / 票据)。"""

    __tablename__ = "case_files"

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 7 种文件类型:jewelry_natural_light / jewelry_strong_light / jewelry_backlight /
    #              jewelry_detail / certificate / receipt / other_doc
    file_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )

    original_filename: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    mime_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    # === OSS 对象键(文件不进 DB,只存 key)===
    oss_bucket: Mapped[str] = mapped_column(
        String(80), nullable=False
    )
    oss_key_original: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    oss_key_preview: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    oss_key_watermarked: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 图片尺寸(图片类型才填)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 上传状态:pending(预签名已发)→ uploaded(回调来)→ processing(转码中)
    #          → ready(可用)/ failed
    upload_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # 是否私有(始终 True,留位防未来公共素材场景)
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    case: Mapped[Case] = relationship(back_populates="files")

    __table_args__ = (Index("idx_case_files_case", "case_id"),)
