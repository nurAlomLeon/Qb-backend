from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.university import University
from app.schemas.common import Envelope
from app.schemas.content import SearchResultOut
from app.services import search as search_service

router = APIRouter(tags=["search"])


@router.get("/search", response_model=Envelope[List[SearchResultOut]])
def search(
    q: str = Query(min_length=2, max_length=120),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[List[SearchResultOut]]:
    return Envelope(
        data=search_service.search_questions(db, tenant.id, q, limit)
    )
