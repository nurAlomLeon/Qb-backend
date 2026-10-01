from __future__ import annotations

import re

from sqlalchemy import select

from app.models.university import AppKey


def _login(ctx):
    response = ctx.client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin-pass"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.text


def _csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "csrf token missing from page"
    return match.group(1)


def test_admin_requires_login(ctx):
    response = ctx.client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code in (302, 303)


def test_admin_login_and_dashboard(ctx):
    _login(ctx)
    response = ctx.client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Questions" in response.text


def test_admin_keygen_creates_key(ctx):
    _login(ctx)
    page = ctx.client.get("/admin/keygen")
    assert page.status_code == 200
    assert "App Keys" in page.text

    response = ctx.client.post(
        "/admin/keygen",
        data={"university_id": "1", "label": "staging", "csrf_token": _csrf(page.text)},
    )
    assert response.status_code == 200
    assert "Key created" in response.text

    with ctx.session_factory() as db:
        keys = db.execute(select(AppKey)).scalars().all()
        labels = sorted(key.label for key in keys)
    assert "staging" in labels


def test_admin_import_page_and_csv_upload(ctx):
    _login(ctx)
    page = ctx.client.get("/admin/import")
    assert page.status_code == 200
    assert "Import Questions" in page.text

    csv_body = (
        "serial,subject_code,chapter_bn,stem_bn,stem_en,option_a,option_b,option_c,option_d,"
        "correct,explanation_bn,shortcut_bn,difficulty\n"
        "10,physics,১ম পত্র • অধ্যায় ১,নতুন প্রশ্ন কত?,New question?,এক,দুই,তিন,চার,খ,কারণ একটাই,টিপ,easy\n"
    )
    response = ctx.client.post(
        "/admin/import",
        data={"paper_id": "1", "subject_code": "", "csrf_token": _csrf(page.text)},
        files={"file": ("questions.csv", csv_body.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200
    assert "Import finished" in response.text
    assert "Created: <strong>1</strong>" in response.text

    questions = ctx.client.get(
        "/api/v1/papers/1/questions?limit=50", headers=ctx.du_headers
    ).json()
    serials = [item["serial"] for item in questions["data"]]
    assert 10 in serials


def test_admin_audit_log_written(ctx):
    _login(ctx)
    page = ctx.client.get("/admin/keygen")
    ctx.client.post(
        "/admin/keygen",
        data={"university_id": "1", "label": "audit-check", "csrf_token": _csrf(page.text)},
    )

    from app.models.admin import AdminAuditLog

    with ctx.session_factory() as db:
        actions = [
            row.action
            for row in db.execute(
                select(AdminAuditLog).order_by(AdminAuditLog.id)
            ).scalars()
        ]
    assert "login" in actions
    assert "app_key.create" in actions
