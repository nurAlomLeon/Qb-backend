from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.university import utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_users_device_id"),
        Index("ix_users_last_seen", "last_seen_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    target_university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id", ondelete="SET NULL"), nullable=True
    )
    target_unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    score_percent: Mapped[int] = mapped_column(Integer, default=0)
    weekly_solved: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    bookmarks: Mapped[List["Bookmark"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_bookmarks_user_question"),
        Index("ix_bookmarks_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    user: Mapped[User] = relationship(back_populates="bookmarks")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (
        Index("ix_sessions_user_created", "user_id", "created_at"),
        Index("ix_sessions_paper", "paper_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE")
    )
    answered: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    wrong: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    answers: Mapped[List["SessionAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionAnswer(Base):
    __tablename__ = "session_answers"
    __table_args__ = (
        Index("ix_answers_session", "session_id"),
        Index("ix_answers_question", "question_id"),
        UniqueConstraint("session_id", "question_id", name="uq_answers_session_question"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    selected_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_spent_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    session: Mapped[PracticeSession] = relationship(back_populates="answers")
