from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _question(source_pk: str = "399548", serial: int = 1) -> dict:
    return {
        "serial": serial,
        "subject_code": "physics",
        "chapter_bn": "১ম পত্র • অধ্যায় ১",
        "stem_bn": "একটি বস্তুর গতিশক্তি কত? (v = 5 m/s)",
        "stem_html": "<p>একটি বস্তুর গতিশক্তি কত? (v = 5 m/s<sup>2</sup>)</p>",
        "options": [
            {"text": "২৫ J", "text_html": "<p>২৫ J</p>"},
            {"text": "৫ J"},
            {"text": "", "image_url": "https://cdn.example.com/eq1.png"},
            {"text": "৫০ J"},
        ],
        "correct_index": 0,
        "explanation_bn": "Ek = ½mv²",
        "explanation_html": "<p>E<sub>k</sub> = ½mv<sup>2</sup></p>",
        "difficulty": "easy",
        "mark": 2.5,
        "source": "aapathshala",
        "source_pk": source_pk,
        "images": ["https://cdn.example.com/figure1.png"],
        "tags": {"year": "2023", "subject": "P-1"},
        "raw_json": {"pk": source_pk, "question": "<p>raw</p>"},
    }


def test_admin_api_requires_key(ctx):
    assert ctx.client.get("/api/v1/admin/ping").status_code == 401
    wrong = ctx.client.get(
        "/api/v1/admin/ping", headers={"X-Admin-Key": "nope"}
    )
    assert wrong.status_code == 401
    ok = ctx.client.get("/api/v1/admin/ping", headers=ctx.admin_headers)
    assert ok.status_code == 200
    data = ok.json()["data"]
    assert data["ok"] is True
    assert data["universities"] == 2


def test_admin_api_disabled_without_key():
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        secret_key="x",
        admin_session_secret="y",
        admin_api_key="",
    )
    app = create_app(settings=settings)
    client = TestClient(app)
    assert client.get("/api/v1/admin/ping").status_code == 503


def test_admin_create_content_is_idempotent(ctx):
    created = ctx.client.post(
        "/api/v1/admin/universities",
        json={"slug": "ju", "name_bn": "জাহাঙ্গীরনগর বিশ্ববিদ্যালয়", "name_en": "Jahangirnagar University"},
        headers=ctx.admin_headers,
    )
    assert created.status_code == 201
    university_id = created.json()["data"]["id"]

    again = ctx.client.post(
        "/api/v1/admin/universities",
        json={"slug": "ju", "name_bn": "জাহাঙ্গীরনগর বিশ্ববিদ্যালয়", "name_en": "Jahangirnagar University"},
        headers=ctx.admin_headers,
    )
    assert again.status_code == 200
    assert again.json()["data"]["id"] == university_id

    unit = ctx.client.post(
        "/api/v1/admin/units",
        json={
            "university_id": university_id,
            "letter": "ক",
            "title_bn": "ক ইউনিট",
            "faculty_bn": "গাণিতিক ও পদার্থবিষয়ক অনুষদ",
            "subjects_label": "পদার্থ • রসায়ন • গণিত",
        },
        headers=ctx.admin_headers,
    )
    assert unit.status_code == 201
    unit_id = unit.json()["data"]["id"]

    subject = ctx.client.post(
        "/api/v1/admin/subjects",
        json={"code": "zoology", "label_bn": "প্রাণিবিদ্যা", "label_en": "Zoology"},
        headers=ctx.admin_headers,
    )
    assert subject.status_code == 201

    paper = ctx.client.post(
        "/api/v1/admin/papers",
        json={
            "university_id": university_id,
            "unit_id": unit_id,
            "year": 2024,
            "label_bn": "২০২৩-২৪ শিক্ষাবর্ষ",
            "question_count": 0,
        },
        headers=ctx.admin_headers,
    )
    assert paper.status_code == 201

    units = ctx.client.get(
        "/api/v1/admin/universities/{id}/units".format(id=university_id),
        headers=ctx.admin_headers,
    ).json()["data"]
    assert len(units) == 1

    papers = ctx.client.get(
        "/api/v1/admin/units/{id}/papers".format(id=unit_id),
        headers=ctx.admin_headers,
    ).json()["data"]
    assert len(papers) == 1


def test_admin_import_upsert_and_skip(ctx):
    paper = ctx.client.post(
        "/api/v1/admin/papers",
        json={
            "university_id": 1,
            "unit_id": 1,
            "year": 2030,
            "label_bn": "২০৩০-৩১ শিক্ষাবর্ষ",
            "question_count": 0,
        },
        headers=ctx.admin_headers,
    ).json()["data"]
    paper_id = paper["id"]

    first = ctx.client.post(
        "/api/v1/admin/papers/{id}/import".format(id=paper_id),
        json={"mode": "upsert", "questions": [_question()]},
        headers=ctx.admin_headers,
    )
    assert first.status_code == 200, first.text
    report = first.json()["data"]
    assert report["created"] == 1
    assert report["updated"] == 0
    assert report["question_count"] == 1

    public = ctx.client.get(
        "/api/v1/papers/{id}/questions?limit=50".format(id=paper_id),
        headers=ctx.du_headers,
    ).json()["data"]
    assert len(public) == 1
    imported = public[0]
    assert imported["images"] == ["https://cdn.example.com/figure1.png"]
    assert imported["options"][2]["image_url"] == "https://cdn.example.com/eq1.png"

    detail = ctx.client.get(
        "/api/v1/questions/{id}".format(id=imported["id"]), headers=ctx.du_headers
    ).json()["data"]
    assert detail["mark"] == 2.5
    assert detail["explanation_bn"] == "Ek = ½mv²"

    second = ctx.client.post(
        "/api/v1/admin/papers/{id}/import".format(id=paper_id),
        json={"mode": "upsert", "questions": [_question(serial=99)]},
        headers=ctx.admin_headers,
    ).json()["data"]
    assert second["created"] == 0
    assert second["updated"] == 1
    assert second["question_count"] == 1

    third = ctx.client.post(
        "/api/v1/admin/papers/{id}/import".format(id=paper_id),
        json={"mode": "skip", "questions": [_question()]},
        headers=ctx.admin_headers,
    ).json()["data"]
    assert third["skipped"] == 1
    assert third["created"] == 0


def test_admin_import_update_keeps_serial_on_collision(ctx):
    # paper 1 already has seeded questions with serials 1..4
    first = ctx.client.post(
        "/api/v1/admin/papers/1/import",
        json={"mode": "upsert", "questions": [_question(source_pk="collision-1", serial=1)]},
        headers=ctx.admin_headers,
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["created"] == 1

    questions = ctx.client.get(
        "/api/v1/papers/1/questions?limit=100", headers=ctx.du_headers
    ).json()["data"]
    imported = next(item for item in questions if item["serial"] > 4)
    assert imported["serial"] == 5

    # re-import the same source_pk with the API serial (1) - must update and
    # keep the assigned serial instead of colliding with the seeded question
    second = ctx.client.post(
        "/api/v1/admin/papers/1/import",
        json={"mode": "upsert", "questions": [_question(source_pk="collision-1", serial=1)]},
        headers=ctx.admin_headers,
    )
    assert second.status_code == 200, second.text
    report = second.json()["data"]
    assert report["created"] == 0
    assert report["updated"] == 1

    questions = ctx.client.get(
        "/api/v1/papers/1/questions?limit=100", headers=ctx.du_headers
    ).json()["data"]
    serials = [item["serial"] for item in questions]
    assert serials.count(5) == 1
    assert 1 in serials  # the seeded question is untouched


def test_admin_import_replace_mode(ctx):
    paper = ctx.client.post(
        "/api/v1/admin/papers",
        json={
            "university_id": 1,
            "unit_id": 1,
            "year": 2031,
            "label_bn": "২০৩০-৩১ শিক্ষাবর্ষ",
            "question_count": 0,
        },
        headers=ctx.admin_headers,
    ).json()["data"]
    paper_id = paper["id"]

    ctx.client.post(
        "/api/v1/admin/papers/{id}/import".format(id=paper_id),
        json={
            "mode": "upsert",
            "questions": [_question(source_pk="r-1", serial=1), _question(source_pk="r-2", serial=2)],
        },
        headers=ctx.admin_headers,
    )

    replaced = ctx.client.post(
        "/api/v1/admin/papers/{id}/import".format(id=paper_id),
        json={"mode": "replace", "questions": [_question(source_pk="r-3", serial=1)]},
        headers=ctx.admin_headers,
    )
    assert replaced.status_code == 200, replaced.text
    report = replaced.json()["data"]
    assert report["created"] == 1
    assert report["question_count"] == 1

    questions = ctx.client.get(
        "/api/v1/papers/{id}/questions?limit=50".format(id=paper_id),
        headers=ctx.du_headers,
    ).json()["data"]
    assert len(questions) == 1
    assert questions[0]["serial"] == 1


def test_admin_import_reports_bad_rows(ctx):
    response = ctx.client.post(
        "/api/v1/admin/papers/1/import",
        json={
            "mode": "upsert",
            "questions": [
                {
                    "subject_code": "does-not-exist",
                    "stem_bn": "bad subject",
                    "options": [{"text": "a"}, {"text": "b"}],
                    "correct_index": 0,
                },
                {
                    "subject_code": "physics",
                    "stem_bn": "one option only",
                    "options": [{"text": "a"}],
                    "correct_index": 0,
                },
            ],
        },
        headers=ctx.admin_headers,
    )
    report = response.json()["data"]
    assert report["created"] == 0
    assert report["skipped"] == 2
    assert len(report["errors"]) == 2


def test_admin_import_unknown_paper(ctx):
    response = ctx.client.post(
        "/api/v1/admin/papers/99999/import",
        json={"mode": "upsert", "questions": []},
        headers=ctx.admin_headers,
    )
    assert response.status_code == 404
