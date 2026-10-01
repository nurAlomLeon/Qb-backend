from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_tenant
from app.models.university import University
from app.models.user import User
from app.schemas.common import Envelope
from app.schemas.user import SessionSubmitIn, SessionSubmitOut
from app.services import sessions as session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=Envelope[SessionSubmitOut], status_code=201)
def submit_session(
    payload: SessionSubmitIn,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
    user: User = Depends(get_current_user),
) -> Envelope[SessionSubmitOut]:
    try:
        result = session_service.submit_session(db, user, tenant.id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return Envelope(data=result)
