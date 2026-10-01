from __future__ import annotations


def test_live_exams_listed_with_statuses_and_order(ctx):
    response = ctx.client.get("/api/v1/live-exams", headers=ctx.du_headers)
    assert response.status_code == 200
    exams = response.json()["data"]

    titles = [exam["title_bn"] for exam in exams]
    assert "অপ্রকাশিত মডেল টেস্ট" not in titles
    assert len(exams) == 3

    assert [exam["status"] for exam in exams] == ["live", "upcoming", "ended"]

    live = exams[0]
    assert live["title_bn"] == "লাইভ মডেল টেস্ট"
    assert live["unit_title_bn"] == "ক ইউনিট"
    assert live["question_count"] == 4
    assert live["participants"] == 500
    assert live["starts_at"] is not None
    assert live["ends_at"] is not None


def test_live_exams_tenant_isolation(ctx):
    exams = ctx.client.get("/api/v1/live-exams", headers=ctx.ru_headers).json()["data"]
    assert len(exams) == 1
    assert exams[0]["title_bn"] == "RU লাইভ মডেল টেস্ট"
    assert exams[0]["status"] == "live"


def test_live_exams_require_app_key(ctx):
    assert ctx.client.get("/api/v1/live-exams").status_code == 401
