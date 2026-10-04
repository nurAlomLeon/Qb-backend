from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Paper, Question, Subject, Unit
from app.schemas.content import (
    OptionOut,
    PaperDetailOut,
    PaperOut,
    QuestionDetailOut,
    QuestionSummaryOut,
    SubjectBreakdownOut,
    UnitOut,
)


def unit_counts(db: Session, university_id: int) -> dict:
    rows = db.execute(
        select(
            Paper.unit_id,
            func.count(Paper.id),
            func.coalesce(func.sum(Paper.question_count), 0),
        )
        .where(
            Paper.university_id == university_id,
            Paper.is_published.is_(True),
        )
        .group_by(Paper.unit_id)
    ).all()
    return {
        unit_id: (paper_count, question_count)
        for unit_id, paper_count, question_count in rows
    }


def list_units(db: Session, university_id: int) -> List[UnitOut]:
    units = (
        db.execute(
            select(Unit)
            .where(
                Unit.university_id == university_id,
                Unit.is_active.is_(True),
            )
            .order_by(Unit.sort_order, Unit.id)
        )
        .scalars()
        .all()
    )
    counts = unit_counts(db, university_id)
    result: List[UnitOut] = []
    for unit in units:
        paper_count, question_count = counts.get(unit.id, (0, 0))
        model = UnitOut.model_validate(unit)
        result.append(
            model.model_copy(
                update={
                    "paper_count": paper_count,
                    "year_count": paper_count,
                    "question_count": int(question_count),
                }
            )
        )
    return result


def list_papers(db: Session, university_id: int, unit_id: int) -> List[PaperOut]:
    papers = (
        db.execute(
            select(Paper)
            .where(
                Paper.university_id == university_id,
                Paper.unit_id == unit_id,
                Paper.is_published.is_(True),
            )
            .order_by(Paper.year.desc())
        )
        .scalars()
        .all()
    )
    return [PaperOut.model_validate(paper) for paper in papers]


def paper_subjects(db: Session, paper_id: int) -> List[SubjectBreakdownOut]:
    rows = db.execute(
        select(Subject.code, Subject.label_bn, func.count(Question.id))
        .join(Question, Question.subject_id == Subject.id)
        .where(Question.paper_id == paper_id, Question.is_published.is_(True))
        .group_by(Subject.id)
        .order_by(Subject.sort_order, Subject.id)
    ).all()
    return [
        SubjectBreakdownOut(code=code, label_bn=label_bn, question_count=count)
        for code, label_bn, count in rows
    ]


def get_paper(db: Session, university_id: int, paper_id: int) -> Optional[Paper]:
    return db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.university_id == university_id,
            Paper.is_published.is_(True),
        )
    ).scalar_one_or_none()


def paper_detail(db: Session, paper: Paper) -> PaperDetailOut:
    model = PaperDetailOut.model_validate(paper)
    return model.model_copy(update={"subjects": paper_subjects(db, paper.id)})


def resolve_subject(db: Session, code: str) -> Optional[Subject]:
    return db.execute(
        select(Subject).where(Subject.code == code)
    ).scalar_one_or_none()


def list_questions(
    db: Session,
    paper: Paper,
    subject_id: Optional[int],
    after_serial: int,
    limit: int,
) -> Tuple[List[Question], int, Optional[int]]:
    filters = [
        Question.paper_id == paper.id,
        Question.is_published.is_(True),
    ]
    if subject_id is not None:
        filters.append(Question.subject_id == subject_id)

    total = (
        db.scalar(select(func.count(Question.id)).where(*filters)) or 0
    )

    rows = (
        db.execute(
            select(Question)
            .options(selectinload(Question.options), selectinload(Question.subject))
            .where(*filters, Question.serial > after_serial)
            .order_by(Question.serial)
            .limit(limit + 1)
        )
        .scalars()
        .all()
    )

    has_more = len(rows) > limit
    page = list(rows[:limit])
    next_after = page[-1].serial if has_more and page else None
    return page, int(total), next_after


def get_question(
    db: Session, university_id: int, question_id: int
) -> Optional[Question]:
    return db.execute(
        select(Question)
        .options(selectinload(Question.options), selectinload(Question.subject))
        .where(
            Question.id == question_id,
            Question.university_id == university_id,
            Question.is_published.is_(True),
        )
    ).scalar_one_or_none()


def question_summary(question: Question) -> QuestionSummaryOut:
    images = question.images
    return QuestionSummaryOut(
        id=question.id,
        paper_id=question.paper_id,
        serial=question.serial,
        subject_code=question.subject.code,
        subject_label_bn=question.subject.label_bn,
        chapter_bn=question.chapter_bn,
        stem_bn=question.stem_bn,
        stem_en=question.stem_en,
        difficulty=question.difficulty,
        analytics_percent=question.analytics_percent,
        options=[OptionOut.model_validate(option) for option in question.options],
        images=[str(url) for url in images] if isinstance(images, list) else [],
    )


def question_detail(question: Question) -> QuestionDetailOut:
    summary = question_summary(question)
    options: Sequence = question.options
    correct_letter = (
        options[question.correct_index].letter
        if 0 <= question.correct_index < len(options)
        else ""
    )
    explanation_images = question.explanation_images
    return QuestionDetailOut(
        **summary.model_dump(),
        correct_index=question.correct_index,
        correct_letter=correct_letter,
        explanation_bn=question.explanation_bn,
        explanation_en=question.explanation_en,
        shortcut_bn=question.shortcut_bn,
        mark=question.mark,
        explanation_images=(
            [str(url) for url in explanation_images]
            if isinstance(explanation_images, list)
            else []
        ),
    )
