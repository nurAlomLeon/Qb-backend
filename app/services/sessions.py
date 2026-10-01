from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content import Paper, Question, Subject, Unit
from app.models.user import PracticeSession, SessionAnswer, User
from app.schemas.user import ProgressRecentOut, ProgressStatsOut, SessionSubmitOut

NEGATIVE_MARK = 0.25


def _refresh_user_stats(db: Session, user: User) -> None:
    answered, correct = db.execute(
        select(
            func.coalesce(func.sum(PracticeSession.answered), 0),
            func.coalesce(func.sum(PracticeSession.correct), 0),
        ).where(PracticeSession.user_id == user.id)
    ).one()
    user.score_percent = round(correct * 100 / answered) if answered else 0

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly = db.scalar(
        select(func.coalesce(func.sum(PracticeSession.answered), 0)).where(
            PracticeSession.user_id == user.id,
            PracticeSession.created_at >= week_ago,
        )
    )
    user.weekly_solved = int(weekly or 0)


def submit_session(
    db: Session, user: User, tenant_university_id: int, payload
) -> SessionSubmitOut:
    paper = db.get(Paper, payload.paper_id)
    if paper is None or paper.university_id != tenant_university_id:
        raise LookupError("paper_not_found")

    questions = (
        db.execute(select(Question).where(Question.paper_id == paper.id))
        .scalars()
        .all()
    )
    by_id = {question.id: question for question in questions}

    correct = 0
    wrong = 0
    answers = []
    for item in payload.answers:
        question = by_id.get(item.question_id)
        if question is None:
            continue
        is_correct = (
            item.selected_index is not None
            and item.selected_index == question.correct_index
        )
        if item.selected_index is not None:
            if is_correct:
                correct += 1
            else:
                wrong += 1
            question.analytics_attempts += 1
            if is_correct:
                question.analytics_correct += 1
            question.analytics_percent = round(
                question.analytics_correct * 100 / question.analytics_attempts
            )
        answers.append(
            SessionAnswer(
                question_id=question.id,
                selected_index=item.selected_index,
                is_correct=is_correct,
                time_spent_ms=item.time_spent_ms,
            )
        )

    answered = correct + wrong
    skipped = max(paper.question_count - answered, 0)
    score = correct - wrong * NEGATIVE_MARK
    accuracy = (correct / answered) if answered else 0.0

    session = PracticeSession(
        user_id=user.id,
        paper_id=paper.id,
        answered=answered,
        correct=correct,
        wrong=wrong,
        skipped=skipped,
        score=score,
        accuracy=accuracy,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
    )
    session.answers = answers
    db.add(session)
    db.flush()

    _refresh_user_stats(db, user)
    db.commit()
    db.refresh(session)

    return SessionSubmitOut(
        session_id=session.id,
        answered=answered,
        correct=correct,
        wrong=wrong,
        skipped=skipped,
        score=score,
        accuracy=accuracy,
        score_percent=user.score_percent,
        weekly_solved=user.weekly_solved,
    )


def recent_progress(db: Session, user: User) -> Optional[ProgressRecentOut]:
    session = db.execute(
        select(PracticeSession)
        .where(PracticeSession.user_id == user.id)
        .order_by(PracticeSession.created_at.desc(), PracticeSession.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if session is None:
        return None

    paper = db.get(Paper, session.paper_id)
    if paper is None:
        return None
    unit = db.get(Unit, paper.unit_id)

    dominant = db.execute(
        select(
            Subject.code,
            Subject.label_bn,
            Question.chapter_bn,
            func.count(SessionAnswer.id).label("answered_count"),
        )
        .join(Question, SessionAnswer.question_id == Question.id)
        .join(Subject, Question.subject_id == Subject.id)
        .where(
            SessionAnswer.session_id == session.id,
            SessionAnswer.selected_index.is_not(None),
        )
        .group_by(Question.chapter_bn)
        .order_by(func.count(SessionAnswer.id).desc())
        .limit(1)
    ).first()

    total = paper.question_count or 0
    percent = round(session.answered * 100 / total) if total else 0
    return ProgressRecentOut(
        session_id=session.id,
        unit_id=paper.unit_id,
        unit_title_bn=unit.title_bn if unit else "",
        year_label=paper.label_bn.replace(" শিক্ষাবর্ষ", "").strip(),
        paper_id=paper.id,
        subject_code=dominant[0] if dominant else None,
        subject_label_bn=dominant[1] if dominant else None,
        chapter_bn=dominant[2] if dominant else None,
        answered=session.answered,
        total=total,
        percent=percent,
    )


def stats(db: Session, user: User) -> ProgressStatsOut:
    sessions, answered, correct = db.execute(
        select(
            func.count(PracticeSession.id),
            func.coalesce(func.sum(PracticeSession.answered), 0),
            func.coalesce(func.sum(PracticeSession.correct), 0),
        ).where(PracticeSession.user_id == user.id)
    ).one()
    return ProgressStatsOut(
        score_percent=user.score_percent,
        weekly_solved=user.weekly_solved,
        total_sessions=int(sessions or 0),
        total_answered=int(answered or 0),
        total_correct=int(correct or 0),
    )
