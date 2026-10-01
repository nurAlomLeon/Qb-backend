from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Request
from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend

from app.core.security import verify_password
from app.models.admin import AdminAuditLog, AdminUser


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str, session_factory) -> None:
        super().__init__(secret_key=secret_key)
        self.session_factory = session_factory

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))

        with self.session_factory() as db:
            user = db.execute(
                select(AdminUser).where(
                    AdminUser.username == username,
                    AdminUser.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if user is None or not verify_password(password, user.password_hash):
                return False

            request.session.update(
                {
                    "admin_user_id": user.id,
                    "admin_username": user.username,
                    "admin_role": user.role,
                    "admin_university_id": user.university_id,
                }
            )
            db.add(
                AdminAuditLog(
                    admin_user_id=user.id,
                    action="login",
                    entity="admin_users",
                    entity_id=user.id,
                )
            )
            db.commit()
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_user_id") is not None


def current_admin_id(request: Request) -> Optional[int]:
    value = request.session.get("admin_user_id")
    return int(value) if value is not None else None


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return str(token)


def verify_csrf(request: Request, form) -> bool:
    expected = request.session.get("csrf_token")
    provided = form.get("csrf_token")
    if not expected or not provided:
        return False
    return secrets.compare_digest(str(expected), str(provided))


def log_admin_action(
    request: Request,
    db,
    action: str,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    detail: Optional[dict] = None,
) -> None:
    db.add(
        AdminAuditLog(
            admin_user_id=current_admin_id(request),
            action=action,
            entity=entity,
            entity_id=entity_id,
            detail=detail,
        )
    )
    db.commit()
