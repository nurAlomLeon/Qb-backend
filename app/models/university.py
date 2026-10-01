from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_bn: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    theme: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class AppKey(Base):
    __tablename__ = "app_keys"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_app_keys_key_hash"),
        UniqueConstraint("university_id", "label", name="uq_app_keys_university_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True
    )
    key_hash: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(80), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class AppConfig(Base):
    __tablename__ = "app_config"
    __table_args__ = (
        UniqueConstraint("university_id", name="uq_app_config_university"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE")
    )
    min_app_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    latest_app_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    force_update: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ContentMeta(Base):
    __tablename__ = "content_meta"
    __table_args__ = (
        UniqueConstraint("university_id", name="uq_content_meta_university"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE")
    )
    content_version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
