from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db, get_tenant
from app.core.config import Settings
from app.core.security import create_device_token
from app.models.university import University
from app.models.university import utcnow
from app.models.user import User
from app.schemas.common import Envelope
from app.schemas.user import DeviceRegisterIn, DeviceRegisterOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/device", response_model=Envelope[DeviceRegisterOut])
def register_device(
    payload: DeviceRegisterIn,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
    settings: Settings = Depends(get_app_settings),
) -> Envelope[DeviceRegisterOut]:
    user = db.execute(
        select(User).where(User.device_id == payload.device_id)
    ).scalar_one_or_none()

    target_university_id = tenant.id
    if payload.target_university_slug:
        target = db.execute(
            select(University).where(
                University.slug == payload.target_university_slug,
                University.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if target is not None:
            target_university_id = target.id

    if user is None:
        user = User(
            device_id=payload.device_id,
            display_name=payload.display_name,
            target_university_id=target_university_id,
            target_unit_id=payload.target_unit_id,
            last_seen_at=utcnow(),
        )
        db.add(user)
    else:
        if payload.display_name:
            user.display_name = payload.display_name
        if payload.target_unit_id:
            user.target_unit_id = payload.target_unit_id
        user.last_seen_at = utcnow()

    db.commit()
    db.refresh(user)

    token = create_device_token(user.device_id, settings)
    return Envelope(
        data=DeviceRegisterOut(token=token, user=UserOut.model_validate(user))
    )
