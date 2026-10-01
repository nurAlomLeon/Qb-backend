from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_app_key, parse_device_token
from app.models.university import AppKey, University
from app.models.user import User


def get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status_code=401, detail=message)


def get_tenant(
    x_app_key: Optional[str] = Header(default=None, alias="X-App-Key"),
    db: Session = Depends(get_db),
) -> University:
    if not x_app_key:
        raise _unauthorized("Missing X-App-Key header.")

    row = db.execute(
        select(University)
        .join(AppKey, AppKey.university_id == University.id)
        .where(
            AppKey.key_hash == hash_app_key(x_app_key),
            AppKey.is_active.is_(True),
            University.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=403, detail="Invalid or inactive app key.")
    return row


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token.")

    token = authorization.split(" ", 1)[1].strip()
    device_id = parse_device_token(token, settings)
    if not device_id:
        raise _unauthorized("Invalid or expired token.")

    user = db.execute(
        select(User).where(User.device_id == device_id)
    ).scalar_one_or_none()
    if user is None:
        raise _unauthorized("Unknown device.")

    now = datetime.now(timezone.utc)
    last_seen = user.last_seen_at
    if last_seen is not None and last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    if last_seen is None or now - last_seen > timedelta(hours=1):
        user.last_seen_at = now
        db.commit()

    return user
