from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.university import University
from app.schemas.common import Envelope
from app.schemas.content import LiveExamOut
from app.services import live_exams as live_exam_service

router = APIRouter(tags=["live-exams"])


@router.get("/live-exams", response_model=Envelope[List[LiveExamOut]])
def list_live_exams(
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[List[LiveExamOut]]:
    return Envelope(data=live_exam_service.list_live_exams(db, tenant.id))
