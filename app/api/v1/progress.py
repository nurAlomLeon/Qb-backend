from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import Envelope
from app.schemas.user import ProgressRecentOut, ProgressStatsOut
from app.services import sessions as session_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/recent", response_model=Envelope[Optional[ProgressRecentOut]])
def recent_progress(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Envelope[Optional[ProgressRecentOut]]:
    return Envelope(data=session_service.recent_progress(db, user))


@router.get("/stats", response_model=Envelope[ProgressStatsOut])
def progress_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Envelope[ProgressStatsOut]:
    return Envelope(data=session_service.stats(db, user))
