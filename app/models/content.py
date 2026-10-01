from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.university import utcnow


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("university_id", "letter", name="uq_units_university_letter"),
        Index("ix_units_university_sort", "university_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True
    )
    letter: Mapped[str] = mapped_column(String(8))
    title_bn: Mapped[str] = mapped_column(String(80))
    title_en: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    faculty_bn: Mapped[str] = mapped_column(String(120))
    subjects_label: Mapped[str] = mapped_column(String(160))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    papers: Mapped[List["Paper"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("code", name="uq_subjects_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True)
    label_bn: Mapped[str] = mapped_column(String(80))
    label_en: Mapped[str] = mapped_column(String(80))
    icon: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (
        UniqueConstraint("unit_id", "year", name="uq_papers_unit_year"),
        Index("ix_papers_university_published", "university_id", "is_published"),
        Index("ix_papers_unit_year", "unit_id", "year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True
    )
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer)
    label_bn: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24), default="fresh")
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    subjects_label: Mapped[str] = mapped_column(String(200))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    unit: Mapped[Unit] = relationship(back_populates="papers")
    questions: Mapped[List["Question"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("paper_id", "serial", name="uq_questions_paper_serial"),
        Index(
            "ix_questions_paper_subject_serial",
            "paper_id",
            "subject_id",
            "serial",
        ),
        Index(
            "ix_questions_university_published_updated",
            "university_id",
            "is_published",
            "updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True
    )
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True
    )
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), index=True
    )
    serial: Mapped[int] = mapped_column(Integer)
    chapter_bn: Mapped[str] = mapped_column(String(160))
    stem_bn: Mapped[str] = mapped_column(Text)
    stem_en: Mapped[str] = mapped_column(Text, default="")
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation_bn: Mapped[str] = mapped_column(Text, default="")
    explanation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shortcut_bn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    analytics_percent: Mapped[int] = mapped_column(Integer, default=0)
    analytics_attempts: Mapped[int] = mapped_column(Integer, default=0)
    analytics_correct: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    paper: Mapped[Paper] = relationship(back_populates="questions")
    subject: Mapped[Subject] = relationship()
    options: Mapped[List["QuestionOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.sort_order",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "letter", name="uq_options_question_letter"),
        Index("ix_options_question_sort", "question_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    letter: Mapped[str] = mapped_column(String(4))
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship(back_populates="options")
