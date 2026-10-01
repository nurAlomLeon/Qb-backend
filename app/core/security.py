from __future__ import annotations

import hashlib
import secrets
from typing import Optional

import bcrypt
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import Settings


def generate_app_key() -> str:
    return "qb_" + secrets.token_urlsafe(32)


def hash_app_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def _device_serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.secret_key,
        salt=settings.device_token_salt,
    )


def create_device_token(device_id: str, settings: Settings) -> str:
    return _device_serializer(settings).dumps({"device_id": device_id})


def parse_device_token(token: str, settings: Settings) -> Optional[str]:
    try:
        payload = _device_serializer(settings).loads(token)
    except BadSignature:
        return None
    if not isinstance(payload, dict):
        return None
    device_id = payload.get("device_id")
    return device_id if isinstance(device_id, str) and device_id else None
