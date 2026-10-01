from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.university import utcnow


class LiveExam(Base):
    __tablename__ = "live_exams"
    __table_args__ = (
        Index(
            "ix_live_exams_university_published_starts",
            "university_id",
            "is_published",
            "starts_at",
        ),
        Index("ix_live_exams_paper", "paper_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True
    )
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE")
    )
    title_bn: Mapped[str] = mapped_column(String(160))
    subtitle_bn: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    question_count: Mapped[int] = mapped_column(Integer, default=100)
    participants: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
