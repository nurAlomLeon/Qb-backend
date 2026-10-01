from __future__ import annotations

from typing import Optional

from sqladmin import BaseView, ModelView, expose
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.admin.auth import csrf_token, log_admin_action, verify_csrf
from app.core.security import generate_app_key, hash_app_key, hash_password
from app.models.admin import AdminAuditLog, AdminUser
from app.models.content import Paper, Question, QuestionOption, Subject, Unit
from app.models.live_exam import LiveExam
from app.models.university import AppConfig, AppKey, ContentMeta, University
from app.models.user import Bookmark, PracticeSession, SessionAnswer, User
from app.services.importing import import_rows, parse_upload


class DbSessionMixin:
    session_factory = None

    def db_session(self):
        factory = type(self).session_factory
        if factory is None:
            raise RuntimeError("session_factory is not configured")
        return factory()


class UniversityAdmin(ModelView, model=University):
    name = "University"
    name_plural = "Universities"
    icon = "fa-solid fa-building-columns"
    column_list = [
        University.id,
        University.slug,
        University.name_bn,
        University.name_en,
        University.is_active,
        University.created_at,
    ]
    column_searchable_list = [University.slug, University.name_bn, University.name_en]
    form_columns = [
        University.slug,
        University.name_bn,
        University.name_en,
        University.logo_url,
        University.theme,
        University.is_active,
    ]


class AppKeyAdmin(ModelView, model=AppKey):
    name = "App Key"
    name_plural = "App Keys"
    icon = "fa-solid fa-key"
    can_create = False
    column_list = [
        AppKey.id,
        AppKey.university_id,
        AppKey.label,
        AppKey.is_active,
        AppKey.created_at,
    ]
    form_columns = [AppKey.label, AppKey.is_active]


class AppConfigAdmin(ModelView, model=AppConfig):
    name = "App Config"
    name_plural = "App Configs"
    icon = "fa-solid fa-sliders"
    column_list = [
        AppConfig.id,
        AppConfig.university_id,
        AppConfig.min_app_version,
        AppConfig.latest_app_version,
        AppConfig.force_update,
        AppConfig.sync_message,
    ]
    form_columns = [
        AppConfig.university_id,
        AppConfig.min_app_version,
        AppConfig.latest_app_version,
        AppConfig.force_update,
        AppConfig.sync_message,
        AppConfig.extra,
    ]


class ContentMetaAdmin(ModelView, model=ContentMeta):
    name = "Content Meta"
    name_plural = "Content Meta"
    icon = "fa-solid fa-code-branch"
    column_list = [
        ContentMeta.id,
        ContentMeta.university_id,
        ContentMeta.content_version,
        ContentMeta.updated_at,
    ]
    form_columns = [ContentMeta.university_id, ContentMeta.content_version]


class UnitAdmin(ModelView, model=Unit):
    name = "Unit"
    name_plural = "Units"
    icon = "fa-solid fa-layer-group"
    column_list = [
        Unit.id,
        Unit.university_id,
        Unit.letter,
        Unit.title_bn,
        Unit.faculty_bn,
        Unit.sort_order,
        Unit.is_active,
    ]
    column_searchable_list = [Unit.title_bn, Unit.faculty_bn]
    column_sortable_list = [Unit.sort_order]
    form_columns = [
        Unit.university_id,
        Unit.letter,
        Unit.title_bn,
        Unit.title_en,
        Unit.faculty_bn,
        Unit.subjects_label,
        Unit.sort_order,
        Unit.is_active,
    ]


class SubjectAdmin(ModelView, model=Subject):
    name = "Subject"
    name_plural = "Subjects"
    icon = "fa-solid fa-book"
    column_list = [
        Subject.id,
        Subject.code,
        Subject.label_bn,
        Subject.label_en,
        Subject.sort_order,
    ]
    column_searchable_list = [Subject.code, Subject.label_bn]
    form_columns = [
        Subject.code,
        Subject.label_bn,
        Subject.label_en,
        Subject.icon,
        Subject.color,
        Subject.sort_order,
    ]


class LiveExamAdmin(ModelView, model=LiveExam):
    name = "Live Exam"
    name_plural = "Live Exams"
    icon = "fa-solid fa-tower-broadcast"
    column_list = [
        LiveExam.id,
        LiveExam.university_id,
        LiveExam.paper_id,
        LiveExam.title_bn,
        LiveExam.starts_at,
        LiveExam.ends_at,
        LiveExam.participants,
        LiveExam.is_published,
    ]
    column_searchable_list = [LiveExam.title_bn]
    column_sortable_list = [LiveExam.starts_at]
    form_columns = [
        LiveExam.university_id,
        LiveExam.paper_id,
        LiveExam.title_bn,
        LiveExam.subtitle_bn,
        LiveExam.starts_at,
        LiveExam.ends_at,
        LiveExam.duration_minutes,
        LiveExam.question_count,
        LiveExam.participants,
        LiveExam.is_published,
    ]


class PaperAdmin(ModelView, model=Paper):
    name = "Paper"
    name_plural = "Papers"
    icon = "fa-solid fa-file-lines"
    column_list = [
        Paper.id,
        Paper.university_id,
        Paper.unit_id,
        Paper.year,
        Paper.label_bn,
        Paper.question_count,
        Paper.is_published,
    ]
    column_searchable_list = [Paper.label_bn]
    column_sortable_list = [Paper.year]
    form_columns = [
        Paper.university_id,
        Paper.unit_id,
        Paper.year,
        Paper.label_bn,
        Paper.status,
        Paper.question_count,
        Paper.duration_minutes,
        Paper.subjects_label,
        Paper.is_published,
    ]


class QuestionOptionInline(ModelView, model=QuestionOption):
    name = "Option"
    name_plural = "Options"
    icon = "fa-solid fa-list"
    column_list = [
        QuestionOption.id,
        QuestionOption.letter,
        QuestionOption.text,
        QuestionOption.sort_order,
    ]
    form_columns = [
        QuestionOption.letter,
        QuestionOption.text,
        QuestionOption.sort_order,
    ]


class QuestionAdmin(DbSessionMixin, ModelView, model=Question):
    name = "Question"
    name_plural = "Questions"
    icon = "fa-solid fa-circle-question"
    column_list = [
        Question.id,
        Question.paper_id,
        Question.serial,
        Question.subject_id,
        Question.difficulty,
        Question.is_published,
    ]
    column_searchable_list = [Question.stem_bn, Question.stem_en, Question.chapter_bn]
    column_sortable_list = [Question.serial, Question.updated_at]
    form_columns = [
        Question.paper_id,
        Question.subject_id,
        Question.serial,
        Question.chapter_bn,
        Question.stem_bn,
        Question.stem_en,
        Question.correct_index,
        Question.explanation_bn,
        Question.explanation_en,
        Question.shortcut_bn,
        Question.difficulty,
        Question.is_published,
    ]
    inline_models = [QuestionOptionInline]

    async def on_model_change(self, data, model, is_created, request) -> None:
        paper_id = data.get("paper_id") or model.paper_id
        if paper_id is not None:
            with self.db_session() as db:
                paper = db.get(Paper, paper_id)
                if paper is not None:
                    data["university_id"] = paper.university_id
                    data["unit_id"] = paper.unit_id


class UserAdmin(ModelView, model=User):
    name = "App User"
    name_plural = "App Users"
    icon = "fa-solid fa-user"
    can_create = False
    column_list = [
        User.id,
        User.device_id,
        User.display_name,
        User.target_university_id,
        User.score_percent,
        User.weekly_solved,
        User.last_seen_at,
    ]
    column_searchable_list = [User.device_id, User.display_name]
    form_columns = [
        User.display_name,
        User.target_university_id,
        User.target_unit_id,
    ]


class BookmarkAdmin(ModelView, model=Bookmark):
    name = "Bookmark"
    name_plural = "Bookmarks"
    icon = "fa-solid fa-bookmark"
    can_create = False
    column_list = [
        Bookmark.id,
        Bookmark.user_id,
        Bookmark.question_id,
        Bookmark.created_at,
    ]


class PracticeSessionAdmin(ModelView, model=PracticeSession):
    name = "Session"
    name_plural = "Practice Sessions"
    icon = "fa-solid fa-stopwatch"
    can_create = False
    column_list = [
        PracticeSession.id,
        PracticeSession.user_id,
        PracticeSession.paper_id,
        PracticeSession.answered,
        PracticeSession.correct,
        PracticeSession.wrong,
        PracticeSession.score,
        PracticeSession.created_at,
    ]
    column_sortable_list = [PracticeSession.created_at]


class SessionAnswerAdmin(ModelView, model=SessionAnswer):
    name = "Session Answer"
    name_plural = "Session Answers"
    icon = "fa-solid fa-check-double"
    can_create = False
    column_list = [
        SessionAnswer.id,
        SessionAnswer.session_id,
        SessionAnswer.question_id,
        SessionAnswer.selected_index,
        SessionAnswer.is_correct,
    ]


class AdminUserAdmin(ModelView, model=AdminUser):
    name = "Admin User"
    name_plural = "Admin Users"
    icon = "fa-solid fa-user-shield"
    column_list = [
        AdminUser.id,
        AdminUser.username,
        AdminUser.role,
        AdminUser.university_id,
        AdminUser.is_active,
    ]
    column_searchable_list = [AdminUser.username]
    form_columns = [
        AdminUser.username,
        AdminUser.password_hash,
        AdminUser.role,
        AdminUser.university_id,
        AdminUser.is_active,
    ]

    async def on_model_change(self, data, model, is_created, request) -> None:
        password = data.get("password_hash")
        if password and not str(password).startswith("$2"):
            data["password_hash"] = hash_password(str(password))


class AdminAuditLogAdmin(ModelView, model=AdminAuditLog):
    name = "Audit Log"
    name_plural = "Audit Log"
    icon = "fa-solid fa-clipboard-list"
    can_create = False
    can_edit = False
    column_list = [
        AdminAuditLog.id,
        AdminAuditLog.admin_user_id,
        AdminAuditLog.action,
        AdminAuditLog.entity,
        AdminAuditLog.entity_id,
        AdminAuditLog.created_at,
    ]
    column_sortable_list = [AdminAuditLog.created_at]


class DashboardView(DbSessionMixin, BaseView):
    name = "Dashboard"
    icon = "fa-solid fa-gauge-high"

    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request: Request) -> HTMLResponse:
        with self.db_session() as db:
            stats = {
                "universities": db.scalar(select(func.count(University.id))) or 0,
                "units": db.scalar(select(func.count(Unit.id))) or 0,
                "papers": db.scalar(select(func.count(Paper.id))) or 0,
                "questions": db.scalar(select(func.count(Question.id))) or 0,
                "users": db.scalar(select(func.count(User.id))) or 0,
                "bookmarks": db.scalar(select(func.count(Bookmark.id))) or 0,
                "sessions": db.scalar(select(func.count(PracticeSession.id))) or 0,
            }
            recent_sessions = (
                db.execute(
                    select(PracticeSession)
                    .order_by(PracticeSession.created_at.desc())
                    .limit(8)
                )
                .scalars()
                .all()
            )
            recent_users = (
                db.execute(
                    select(User).order_by(User.last_seen_at.desc()).limit(5)
                )
                .scalars()
                .all()
            )
        return await self.templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "stats": stats,
                "recent_sessions": recent_sessions,
                "recent_users": recent_users,
            },
        )


class KeygenView(DbSessionMixin, BaseView):
    name = "App Keys"
    icon = "fa-solid fa-key"

    @expose("/keygen", methods=["GET"])
    async def keygen_form(self, request: Request) -> HTMLResponse:
        return await self._render(request)

    @expose("/keygen", methods=["POST"])
    async def keygen_create(self, request: Request) -> HTMLResponse:
        form = await request.form()
        if not verify_csrf(request, form):
            return await self._render(request, error="Invalid CSRF token, retry.")
        university_id = int(str(form.get("university_id") or "0"))
        label = str(form.get("label") or "default").strip() or "default"

        with self.db_session() as db:
            university = db.get(University, university_id)
            if university is None:
                return await self._render(
                    request, error="Select a valid university."
                )
            raw_key = generate_app_key()
            db.add(
                AppKey(
                    university_id=university_id,
                    key_hash=hash_app_key(raw_key),
                    label=label,
                )
            )
            log_admin_action(
                request,
                db,
                action="app_key.create",
                entity="app_keys",
                detail={"university_id": university_id, "label": label},
            )
        return await self._render(request, created_key=raw_key, created_label=label)

    async def _render(
        self,
        request: Request,
        created_key: Optional[str] = None,
        created_label: Optional[str] = None,
        error: Optional[str] = None,
    ) -> HTMLResponse:
        with self.db_session() as db:
            universities = (
                db.execute(select(University).order_by(University.slug))
                .scalars()
                .all()
            )
            keys = (
                db.execute(
                    select(AppKey, University)
                    .join(University, AppKey.university_id == University.id)
                    .order_by(AppKey.created_at.desc())
                    .limit(50)
                )
                .all()
            )
        return await self.templates.TemplateResponse(
            request,
            "keys.html",
            {
                "universities": universities,
                "keys": keys,
                "created_key": created_key,
                "created_label": created_label,
                "error": error,
                "csrf_token": csrf_token(request),
            },
        )


class ImportView(DbSessionMixin, BaseView):
    name = "Import Questions"
    icon = "fa-solid fa-file-import"

    @expose("/import", methods=["GET"])
    async def import_form(self, request: Request) -> HTMLResponse:
        return await self._render(request)

    @expose("/import", methods=["POST"])
    async def import_questions(self, request: Request) -> HTMLResponse:
        form = await request.form()
        if not verify_csrf(request, form):
            return await self._render(request, error="Invalid CSRF token, retry.")
        paper_id = int(str(form.get("paper_id") or "0"))
        default_subject = str(form.get("subject_code") or "").strip()
        upload = form.get("file")

        if upload is None or not hasattr(upload, "read"):
            return await self._render(
                request, error="Choose a CSV, XLSX or JSON file."
            )
        data = await upload.read()
        filename = getattr(upload, "filename", "upload.csv") or "upload.csv"

        with self.db_session() as db:
            paper = db.get(Paper, paper_id)
            if paper is None:
                return await self._render(request, error="Select a valid paper.")

            try:
                rows = parse_upload(filename, data)
            except Exception as exc:
                return await self._render(
                    request,
                    error="Could not parse file: {err}".format(err=exc),
                )

            report = import_rows(db, paper, rows, default_subject)
            log_admin_action(
                request,
                db,
                action="questions.import",
                entity="papers",
                entity_id=paper.id,
                detail={
                    "created": report["created"],
                    "updated": report["updated"],
                    "skipped": report["skipped"],
                },
            )

        return await self._render(
            request,
            report={
                "created": report["created"],
                "updated": report["updated"],
                "skipped": report["skipped"],
                "errors": report["errors"][:20],
                "paper_id": paper_id,
            },
        )

    async def _render(
        self,
        request: Request,
        report: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> HTMLResponse:
        with self.db_session() as db:
            papers = (
                db.execute(
                    select(Paper, Unit, University)
                    .join(Unit, Paper.unit_id == Unit.id)
                    .join(University, Paper.university_id == University.id)
                    .order_by(University.slug, Unit.sort_order, Paper.year.desc())
                )
                .all()
            )
            subjects = (
                db.execute(select(Subject).order_by(Subject.sort_order))
                .scalars()
                .all()
            )
        return await self.templates.TemplateResponse(
            request,
            "import.html",
            {
                "papers": papers,
                "subjects": subjects,
                "report": report,
                "error": error,
                "csrf_token": csrf_token(request),
            },
        )
