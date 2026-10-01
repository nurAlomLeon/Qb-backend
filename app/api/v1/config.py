from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.models.university import AppConfig, ContentMeta, University
from app.schemas.common import Envelope, Meta
from app.schemas.content import AppConfigOut, ConfigOut, UniversityOut
from app.services import content as content_service

router = APIRouter(tags=["config"])


@router.get("/config", response_model=Envelope[ConfigOut])
def get_config(
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
) -> Envelope[ConfigOut]:
    config = db.execute(
        select(AppConfig).where(AppConfig.university_id == tenant.id)
    ).scalar_one_or_none()
    config_out = (
        AppConfigOut.model_validate(config)
        if config is not None
        else AppConfigOut(
            min_app_version="1.0.0",
            latest_app_version="1.0.0",
            force_update=False,
        )
    )

    meta_row = db.execute(
        select(ContentMeta).where(ContentMeta.university_id == tenant.id)
    ).scalar_one_or_none()
    content_version = meta_row.content_version if meta_row else 1

    return Envelope(
        data=ConfigOut(
            university=UniversityOut.model_validate(tenant),
            config=config_out,
            units=content_service.list_units(db, tenant.id),
            content_version=content_version,
        ),
        meta=Meta(content_version=content_version),
    )
