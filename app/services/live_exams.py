from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Paper, Unit
from app.models.live_exam import LiveExam
from app.schemas.content import LiveExamOut


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def exam_status(exam: LiveExam, now: datetime) -> str:
    starts_at = _as_utc(exam.starts_at)
    ends_at = _as_utc(exam.ends_at) if exam.ends_at is not None else None

    if ends_at is not None and now > ends_at:
        return "ended"
    if now < starts_at:
        return "upcoming"
    return "live"


def list_live_exams(db: Session, university_id: int) -> List[LiveExamOut]:
    rows = db.execute(
        select(LiveExam, Unit.title_bn)
        .join(Paper, LiveExam.paper_id == Paper.id)
        .join(Unit, Paper.unit_id == Unit.id)
        .where(
            LiveExam.university_id == university_id,
            LiveExam.is_published.is_(True),
            Paper.is_published.is_(True),
        )
        .order_by(LiveExam.starts_at.desc())
    ).all()

    now = datetime.now(timezone.utc)
    result: List[LiveExamOut] = []
    for exam, unit_title in rows:
        result.append(
            LiveExamOut(
                id=exam.id,
                paper_id=exam.paper_id,
                title_bn=exam.title_bn,
                subtitle_bn=exam.subtitle_bn,
                unit_title_bn=unit_title,
                starts_at=exam.starts_at,
                ends_at=exam.ends_at,
                duration_minutes=exam.duration_minutes,
                question_count=exam.question_count,
                participants=exam.participants,
                status=exam_status(exam, now),
            )
        )

    order = {"live": 0, "upcoming": 1, "ended": 2}
    result.sort(key=lambda item: (order.get(item.status, 3), -item.starts_at.timestamp()))
    return result
