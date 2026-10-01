from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.content import Unit
from app.models.university import University
from app.schemas.common import Envelope
from app.schemas.content import PaperDetailOut, PaperOut
from app.services import content as content_service

router = APIRouter(tags=["papers"])


@router.get("/units/{unit_id}/papers", response_model=Envelope[List[PaperOut]])
def list_unit_papers(
    unit_id: int,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[List[PaperOut]]:
    unit = db.get(Unit, unit_id)
    if unit is None or unit.university_id != tenant.id or not unit.is_active:
        raise HTTPException(status_code=404, detail="Unit not found.")
    return Envelope(data=content_service.list_papers(db, tenant.id, unit_id))


@router.get("/papers/{paper_id}", response_model=Envelope[PaperDetailOut])
def get_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[PaperDetailOut]:
    paper = content_service.get_paper(db, tenant.id, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return Envelope(data=content_service.paper_detail(db, paper))
