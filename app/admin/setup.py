from __future__ import annotations

from pathlib import Path

from sqladmin import Admin
from sqlalchemy.engine import Engine

from app.admin import views as admin_views
from app.admin.auth import AdminAuth
from app.core.config import Settings


def setup_admin(app, engine: Engine, settings: Settings) -> None:
    templates_dir = Path(__file__).resolve().parent / "templates"
    session_factory = app.state.session_factory

    admin = Admin(
        app=app,
        engine=engine,
        title="Question Bank Admin",
        base_url="/admin",
        authentication_backend=AdminAuth(
            secret_key=settings.admin_session_secret,
            session_factory=session_factory,
        ),
        templates_dir=str(templates_dir),
    )

    for view_class in (
        admin_views.DashboardView,
        admin_views.KeygenView,
        admin_views.ImportView,
        admin_views.QuestionAdmin,
    ):
        view_class.session_factory = session_factory

    admin.add_view(admin_views.DashboardView)
    admin.add_view(admin_views.KeygenView)
    admin.add_view(admin_views.ImportView)
    admin.add_view(admin_views.UniversityAdmin)
    admin.add_view(admin_views.UnitAdmin)
    admin.add_view(admin_views.SubjectAdmin)
    admin.add_view(admin_views.PaperAdmin)
    admin.add_view(admin_views.LiveExamAdmin)
    admin.add_view(admin_views.QuestionAdmin)
    admin.add_view(admin_views.AppKeyAdmin)
    admin.add_view(admin_views.AppConfigAdmin)
    admin.add_view(admin_views.ContentMetaAdmin)
    admin.add_view(admin_views.UserAdmin)
    admin.add_view(admin_views.BookmarkAdmin)
    admin.add_view(admin_views.PracticeSessionAdmin)
    admin.add_view(admin_views.SessionAnswerAdmin)
    admin.add_view(admin_views.AdminUserAdmin)
    admin.add_view(admin_views.AdminAuditLogAdmin)
