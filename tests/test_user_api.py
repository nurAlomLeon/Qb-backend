from __future__ import annotations

from sqlalchemy import select

from app.models.content import Question
from tests.conftest import register_device


def _paper_id(ctx, year: int = 2024) -> int:
    papers = ctx.client.get("/api/v1/units/1/papers", headers=ctx.du_headers).json()["data"]
    return next(paper["id"] for paper in papers if paper["year"] == year)


def _questions(ctx, paper_id: int):
    return ctx.client.get(
        "/api/v1/papers/{paper_id}/questions".format(paper_id=paper_id),
        headers=ctx.du_headers,
    ).json()["data"]


def test_device_registration_returns_token(ctx):
    response = ctx.client.post(
        "/api/v1/auth/device",
        json={"device_id": "device-abc-123", "display_name": "Rahim"},
        headers=ctx.du_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token"]
    assert data["user"]["device_id"] == "device-abc-123"
    assert data["user"]["target_university_id"] == 1

    again = ctx.client.post(
        "/api/v1/auth/device",
        json={"device_id": "device-abc-123"},
        headers=ctx.du_headers,
    )
    assert again.json()["data"]["user"]["id"] == data["user"]["id"]


def test_user_endpoints_require_token(ctx):
    assert ctx.client.get("/api/v1/bookmarks", headers=ctx.du_headers).status_code == 401
    bad = ctx.client.get(
        "/api/v1/bookmarks",
        headers={**ctx.du_headers, "Authorization": "Bearer nonsense"},
    )
    assert bad.status_code == 401


def test_bookmark_lifecycle(ctx):
    headers = register_device(ctx)
    question = _questions(ctx, _paper_id(ctx))[0]

    created = ctx.client.post(
        "/api/v1/bookmarks",
        json={"question_id": question["id"]},
        headers={**ctx.du_headers, **headers},
    )
    assert created.status_code == 201
    bookmark = created.json()["data"]
    assert bookmark["correct_letter"] == "ক"
    assert bookmark["year_tag"] == "২০২৩-২৪"

    duplicate = ctx.client.post(
        "/api/v1/bookmarks",
        json={"question_id": question["id"]},
        headers={**ctx.du_headers, **headers},
    )
    assert duplicate.status_code == 201

    listed = ctx.client.get(
        "/api/v1/bookmarks", headers={**ctx.du_headers, **headers}
    ).json()["data"]
    assert len(listed) == 1

    removed = ctx.client.delete(
        "/api/v1/bookmarks/{question_id}".format(question_id=question["id"]),
        headers={**ctx.du_headers, **headers},
    )
    assert removed.status_code == 204

    missing = ctx.client.delete(
        "/api/v1/bookmarks/{question_id}".format(question_id=question["id"]),
        headers={**ctx.du_headers, **headers},
    )
    assert missing.status_code == 404


def test_bookmark_rejects_cross_tenant_question(ctx):
    headers = register_device(ctx)
    ru_paper = ctx.client.get("/api/v1/units/2/papers", headers=ctx.ru_headers).json()["data"][0]
    ru_question = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions".format(paper_id=ru_paper["id"]),
        headers=ctx.ru_headers,
    ).json()["data"][0]

    response = ctx.client.post(
        "/api/v1/bookmarks",
        json={"question_id": ru_question["id"]},
        headers={**ctx.du_headers, **headers},
    )
    assert response.status_code == 404


def test_session_submit_scoring_and_progress(ctx):
    headers = register_device(ctx)
    paper_id = _paper_id(ctx)
    questions = _questions(ctx, paper_id)
    assert len(questions) == 3

    answers = [
        {"question_id": questions[0]["id"], "selected_index": 0, "time_spent_ms": 12000},
        {"question_id": questions[1]["id"], "selected_index": 1},
        {"question_id": questions[2]["id"], "selected_index": None},
    ]
    response = ctx.client.post(
        "/api/v1/sessions",
        json={"paper_id": paper_id, "answers": answers},
        headers={**ctx.du_headers, **headers},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["answered"] == 2
    assert data["correct"] == 1
    assert data["wrong"] == 1
    assert data["skipped"] == 2
    assert data["score"] == 0.75
    assert data["accuracy"] == 0.5
    assert data["score_percent"] == 50
    assert data["weekly_solved"] == 2

    with ctx.session_factory() as db:
        question = db.execute(
            select(Question).where(Question.id == questions[0]["id"])
        ).scalar_one()
        assert question.analytics_attempts == 101
        assert question.analytics_correct == 61
        assert question.analytics_percent == 60

    recent = ctx.client.get(
        "/api/v1/progress/recent", headers={**ctx.du_headers, **headers}
    ).json()["data"]
    assert recent["unit_title_bn"] == "ক ইউনিট"
    assert recent["year_label"] == "২০২৩-২৪"
    assert recent["answered"] == 2
    assert recent["total"] == 4
    assert recent["percent"] == 50
    assert recent["subject_code"] == "physics"

    stats = ctx.client.get(
        "/api/v1/progress/stats", headers={**ctx.du_headers, **headers}
    ).json()["data"]
    assert stats["total_sessions"] == 1
    assert stats["total_answered"] == 2
    assert stats["total_correct"] == 1


def test_session_submit_unknown_paper(ctx):
    headers = register_device(ctx)
    response = ctx.client.post(
        "/api/v1/sessions",
        json={"paper_id": 999999, "answers": []},
        headers={**ctx.du_headers, **headers},
    )
    assert response.status_code == 404


def test_progress_recent_empty(ctx):
    headers = register_device(ctx)
    response = ctx.client.get(
        "/api/v1/progress/recent", headers={**ctx.du_headers, **headers}
    )
    assert response.status_code == 200
    assert response.json()["data"] is None
