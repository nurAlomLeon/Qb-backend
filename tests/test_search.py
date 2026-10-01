from __future__ import annotations


def test_search_bangla_stem(ctx):
    response = ctx.client.get("/api/v1/search?q=গতিশক্তি", headers=ctx.du_headers)
    assert response.status_code == 200
    results = response.json()["data"]
    assert len(results) == 1
    assert results[0]["stem_bn"].startswith("ভরবেগ")
    assert results[0]["subject_code"] == "physics"
    assert "…" in results[0]["snippet"] or "গতিশক্তি" in results[0]["snippet"]


def test_search_english_stem(ctx):
    results = ctx.client.get(
        "/api/v1/search?q=momentum", headers=ctx.du_headers
    ).json()["data"]
    assert len(results) == 1
    assert results[0]["serial"] == 1


def test_search_requires_minimum_length(ctx):
    assert (
        ctx.client.get("/api/v1/search?q=x", headers=ctx.du_headers).status_code
        == 422
    )


def test_search_respects_tenant(ctx):
    results = ctx.client.get(
        "/api/v1/search?q=energy", headers=ctx.ru_headers
    ).json()["data"]
    assert len(results) == 1
    assert results[0]["stem_bn"].startswith("রাজশাহী")

    du_results = ctx.client.get(
        "/api/v1/search?q=energy", headers=ctx.du_headers
    ).json()["data"]
    assert len(du_results) == 2


def test_search_no_results(ctx):
    results = ctx.client.get(
        "/api/v1/search?q=zzzzz", headers=ctx.du_headers
    ).json()["data"]
    assert results == []
