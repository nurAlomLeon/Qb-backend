from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.university import University
from app.schemas.common import Envelope
from app.schemas.content import UnitOut
from app.services import content as content_service

router = APIRouter(tags=["units"])


@router.get("/units", response_model=Envelope[List[UnitOut]])
def list_units(
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[List[UnitOut]]:
    return Envelope(data=content_service.list_units(db, tenant.id))
