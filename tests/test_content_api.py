from __future__ import annotations


def test_config_returns_tenant_branding_and_units(ctx):
    response = ctx.client.get("/api/v1/config", headers=ctx.du_headers)
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert data["university"]["slug"] == "du"
    assert data["config"]["latest_app_version"] == "2.4.0"
    assert data["content_version"] == 7
    assert payload["meta"]["content_version"] == 7
    assert len(data["units"]) == 1
    assert data["units"][0]["letter"] == "ক"
    assert data["units"][0]["paper_count"] == 2


def test_missing_or_invalid_app_key(ctx):
    assert ctx.client.get("/api/v1/config").status_code == 401
    assert (
        ctx.client.get("/api/v1/config", headers={"X-App-Key": "nope"}).status_code
        == 403
    )


def test_units_and_papers_ordering(ctx):
    units = ctx.client.get("/api/v1/units", headers=ctx.du_headers).json()["data"]
    assert len(units) == 1
    unit_id = units[0]["id"]

    papers = ctx.client.get(
        "/api/v1/units/{unit_id}/papers".format(unit_id=unit_id),
        headers=ctx.du_headers,
    ).json()["data"]
    assert [paper["year"] for paper in papers] == [2024, 2023]


def test_paper_detail_subject_breakdown(ctx):
    papers = ctx.client.get("/api/v1/units/1/papers", headers=ctx.du_headers).json()["data"]
    paper_id = papers[0]["id"]
    detail = ctx.client.get(
        "/api/v1/papers/{paper_id}".format(paper_id=paper_id),
        headers=ctx.du_headers,
    ).json()["data"]
    breakdown = {item["code"]: item["question_count"] for item in detail["subjects"]}
    assert breakdown == {"physics": 2, "chemistry": 1}


def test_question_keyset_pagination(ctx):
    papers = ctx.client.get("/api/v1/units/1/papers", headers=ctx.du_headers).json()["data"]
    paper_id = papers[0]["id"]

    first = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions?limit=2".format(paper_id=paper_id),
        headers=ctx.du_headers,
    ).json()
    assert [item["serial"] for item in first["data"]] == [1, 2]
    assert first["meta"]["total"] == 3
    assert first["meta"]["has_more"] is True
    assert first["meta"]["next_after_serial"] == 2

    second = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions?limit=2&after_serial=2".format(
            paper_id=paper_id
        ),
        headers=ctx.du_headers,
    ).json()
    assert [item["serial"] for item in second["data"]] == [3]
    assert second["meta"]["has_more"] is False
    assert second["meta"]["next_after_serial"] is None


def test_questions_exclude_unpublished_and_filter_by_subject(ctx):
    papers = ctx.client.get("/api/v1/units/1/papers", headers=ctx.du_headers).json()["data"]
    paper_id = papers[0]["id"]

    chemistry = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions?subject=chemistry".format(paper_id=paper_id),
        headers=ctx.du_headers,
    ).json()
    assert [item["serial"] for item in chemistry["data"]] == [3]
    assert chemistry["meta"]["total"] == 1

    unknown = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions?subject=nope".format(paper_id=paper_id),
        headers=ctx.du_headers,
    )
    assert unknown.status_code == 404


def test_question_detail_includes_answer_and_explanation(ctx):
    papers = ctx.client.get("/api/v1/units/1/papers", headers=ctx.du_headers).json()["data"]
    paper_id = papers[0]["id"]
    questions = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions".format(paper_id=paper_id),
        headers=ctx.du_headers,
    ).json()["data"]
    question_id = questions[0]["id"]

    detail = ctx.client.get(
        "/api/v1/questions/{question_id}".format(question_id=question_id),
        headers=ctx.du_headers,
    ).json()["data"]
    assert detail["correct_index"] == 0
    assert detail["correct_letter"] == "ক"
    assert "ব্যাখ্যা" in detail["explanation_bn"]
    assert len(detail["options"]) == 4


def test_tenant_isolation(ctx):
    ru_papers = ctx.client.get("/api/v1/units", headers=ctx.ru_headers).json()["data"]
    assert ru_papers[0]["paper_count"] == 1

    ru_paper_id = ctx.client.get("/api/v1/units/2/papers", headers=ctx.ru_headers).json()["data"][0]["id"]
    cross = ctx.client.get(
        "/api/v1/papers/{paper_id}".format(paper_id=ru_paper_id),
        headers=ctx.du_headers,
    )
    assert cross.status_code == 404

    ru_question = ctx.client.get(
        "/api/v1/papers/{paper_id}/questions".format(paper_id=ru_paper_id),
        headers=ctx.ru_headers,
    ).json()["data"][0]
    hidden = ctx.client.get(
        "/api/v1/questions/{question_id}".format(question_id=ru_question["id"]),
        headers=ctx.du_headers,
    )
    assert hidden.status_code == 404


def test_error_envelope_shape(ctx):
    response = ctx.client.get("/api/v1/papers/99999", headers=ctx.du_headers)
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "message" in body["error"]


def test_version_endpoint(ctx):
    data = ctx.client.get("/api/v1/version/latest", headers=ctx.du_headers).json()["data"]
    assert data["latest"] == "2.4.0"
    assert data["min_supported"] == "2.0.0"
