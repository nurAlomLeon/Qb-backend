from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db, get_tenant
from app.core.config import Settings
from app.models.university import University
from app.schemas.common import Envelope, Meta
from app.schemas.content import QuestionDetailOut, QuestionSummaryOut
from app.services import content as content_service

router = APIRouter(tags=["questions"])


@router.get(
    "/papers/{paper_id}/questions",
    response_model=Envelope[List[QuestionSummaryOut]],
)
def list_questions(
    paper_id: int,
    subject: Optional[str] = Query(default=None, max_length=32),
    after_serial: int = Query(default=0, ge=0),
    limit: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
    settings: Settings = Depends(get_app_settings),
) -> Envelope[List[QuestionSummaryOut]]:
    paper = content_service.get_paper(db, tenant.id, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    subject_id: Optional[int] = None
    if subject:
        subject_row = content_service.resolve_subject(db, subject)
        if subject_row is None:
            raise HTTPException(status_code=404, detail="Subject not found.")
        subject_id = subject_row.id

    page_size = min(limit or settings.default_page_size, settings.max_page_size)
    rows, total, next_after = content_service.list_questions(
        db, paper, subject_id, after_serial, page_size
    )

    return Envelope(
        data=[content_service.question_summary(question) for question in rows],
        meta=Meta(
            total=total,
            limit=page_size,
            has_more=next_after is not None,
            next_after_serial=next_after,
        ),
    )


@router.get("/questions/{question_id}", response_model=Envelope[QuestionDetailOut])
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[QuestionDetailOut]:
    question = content_service.get_question(db, tenant.id, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return Envelope(data=content_service.question_detail(question))
