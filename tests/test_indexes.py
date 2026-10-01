from __future__ import annotations

from sqlalchemy import text


def _plan(ctx, sql: str, params: dict = None) -> str:
    with ctx.engine.connect() as connection:
        rows = connection.execute(
            text("EXPLAIN QUERY PLAN " + sql), params or {}
        ).all()
    return " ".join(str(row[-1]) for row in rows)


def test_questions_keyset_query_uses_index(ctx):
    plan = _plan(
        ctx,
        "SELECT id FROM questions WHERE paper_id = :paper_id AND serial > :serial "
        "ORDER BY serial LIMIT 25",
        {"paper_id": 1, "serial": 0},
    )
    assert "USING INDEX" in plan or "USING COVERING INDEX" in plan


def test_questions_subject_query_uses_composite_index(ctx):
    plan = _plan(
        ctx,
        "SELECT id FROM questions WHERE paper_id = :paper_id AND subject_id = :subject_id "
        "AND serial > :serial ORDER BY serial LIMIT 25",
        {"paper_id": 1, "subject_id": 1, "serial": 0},
    )
    assert "USING INDEX" in plan or "USING COVERING INDEX" in plan


def test_bookmarks_query_uses_index(ctx):
    plan = _plan(
        ctx,
        "SELECT id FROM bookmarks WHERE user_id = :user_id ORDER BY created_at DESC",
        {"user_id": 1},
    )
    assert "USING INDEX" in plan or "USING COVERING INDEX" in plan


def test_papers_by_unit_uses_index(ctx):
    plan = _plan(
        ctx,
        "SELECT id FROM papers WHERE unit_id = :unit_id ORDER BY year DESC",
        {"unit_id": 1},
    )
    assert "USING INDEX" in plan or "USING COVERING INDEX" in plan


def test_sessions_recent_uses_index(ctx):
    plan = _plan(
        ctx,
        "SELECT id FROM practice_sessions WHERE user_id = :user_id "
        "ORDER BY created_at DESC LIMIT 1",
        {"user_id": 1},
    )
    assert "USING INDEX" in plan or "USING COVERING INDEX" in plan


def test_fts_table_populated_and_searchable(ctx):
    with ctx.engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM questions_fts")
        ).scalar_one()
        matches = connection.execute(
            text(
                "SELECT COUNT(*) FROM questions_fts "
                "WHERE questions_fts MATCH :match"
            ),
            {"match": '"গতিশক্তি"*'},
        ).scalar_one()
    assert count >= 7
    assert matches == 1
