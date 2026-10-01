from __future__ import annotations

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.content import Paper, Question, QuestionOption, Subject, Unit
from app.models.user import Bookmark, User
from app.schemas.user import BookmarkOut


def _year_tag(paper: Paper) -> str:
    return paper.label_bn.replace(" শিক্ষাবর্ষ", "").strip()


def _correct_option(
    question: Question, options_by_question: dict
) -> Optional[QuestionOption]:
    options = options_by_question.get(question.id, [])
    if 0 <= question.correct_index < len(options):
        return options[question.correct_index]
    return None


def list_bookmarks(db: Session, user: User) -> List[BookmarkOut]:
    rows = db.execute(
        select(Bookmark, Question, Paper, Unit, Subject)
        .join(Question, Bookmark.question_id == Question.id)
        .join(Paper, Question.paper_id == Paper.id)
        .join(Unit, Question.unit_id == Unit.id)
        .join(Subject, Question.subject_id == Subject.id)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc(), Bookmark.id.desc())
    ).all()

    question_ids = [question.id for _, question, _, _, _ in rows]
    options_by_question: dict = {}
    if question_ids:
        options = (
            db.execute(
                select(QuestionOption).where(
                    QuestionOption.question_id.in_(question_ids)
                )
            )
            .scalars()
            .all()
        )
        for option in options:
            options_by_question.setdefault(option.question_id, []).append(option)

    result: List[BookmarkOut] = []
    for bookmark, question, paper, _unit, subject in rows:
        options = sorted(
            options_by_question.get(question.id, []),
            key=lambda item: item.sort_order,
        )
        options_by_question[question.id] = options
        correct = _correct_option(question, options_by_question)
        result.append(
            BookmarkOut(
                id=bookmark.id,
                question_id=question.id,
                paper_id=paper.id,
                unit_id=question.unit_id,
                serial=question.serial,
                subject_code=subject.code,
                subject_label_bn=subject.label_bn,
                year_tag=_year_tag(paper),
                stem_bn=question.stem_bn,
                correct_letter=correct.letter if correct else "",
                correct_text=correct.text if correct else "",
                created_at=bookmark.created_at,
            )
        )
    return result


def add_bookmark(db: Session, user: User, question: Question) -> BookmarkOut:
    existing = db.execute(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.question_id == question.id,
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Bookmark(user_id=user.id, question_id=question.id)
        db.add(existing)
        db.commit()
        db.refresh(existing)

    paper = db.get(Paper, question.paper_id)
    subject = db.get(Subject, question.subject_id)
    options = sorted(question.options, key=lambda item: item.sort_order)
    correct = (
        options[question.correct_index]
        if 0 <= question.correct_index < len(options)
        else None
    )
    return BookmarkOut(
        id=existing.id,
        question_id=question.id,
        paper_id=question.paper_id,
        unit_id=question.unit_id,
        serial=question.serial,
        subject_code=subject.code if subject else "",
        subject_label_bn=subject.label_bn if subject else "",
        year_tag=_year_tag(paper) if paper else "",
        stem_bn=question.stem_bn,
        correct_letter=correct.letter if correct else "",
        correct_text=correct.text if correct else "",
        created_at=existing.created_at,
    )


def remove_bookmark(db: Session, user: User, question_id: int) -> bool:
    result = db.execute(
        delete(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.question_id == question_id,
        )
    )
    db.commit()
    return bool(result.rowcount)


def clear_bookmarks(db: Session, user: User) -> int:
    result = db.execute(delete(Bookmark).where(Bookmark.user_id == user.id))
    db.commit()
    return int(result.rowcount or 0)
