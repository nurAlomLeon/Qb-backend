from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.university import AppConfig, University
from app.schemas.common import Envelope
from app.schemas.content import VersionOut

router = APIRouter(tags=["version"])


@router.get("/version/latest", response_model=Envelope[VersionOut])
def latest_version(
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[VersionOut]:
    config = db.execute(
        select(AppConfig).where(AppConfig.university_id == tenant.id)
    ).scalar_one_or_none()
    return Envelope(
        data=VersionOut(
            latest=config.latest_app_version if config else "1.0.0",
            min_supported=config.min_app_version if config else "1.0.0",
            force_update=config.force_update if config else False,
            message=config.sync_message if config else None,
        )
    )
