from __future__ import annotations

from sqlalchemy import Connection, text

FTS_TABLE = "questions_fts"

CREATE_FTS_STATEMENTS = [
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
        stem_bn,
        stem_en,
        chapter_bn,
        content='questions',
        content_rowid='id',
        tokenize='unicode61 remove_diacritics 0'
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS questions_fts_ai AFTER INSERT ON questions BEGIN
        INSERT INTO questions_fts(rowid, stem_bn, stem_en, chapter_bn)
        VALUES (new.id, new.stem_bn, new.stem_en, new.chapter_bn);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS questions_fts_ad AFTER DELETE ON questions BEGIN
        INSERT INTO questions_fts(questions_fts, rowid, stem_bn, stem_en, chapter_bn)
        VALUES ('delete', old.id, old.stem_bn, old.stem_en, old.chapter_bn);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS questions_fts_au AFTER UPDATE ON questions BEGIN
        INSERT INTO questions_fts(questions_fts, rowid, stem_bn, stem_en, chapter_bn)
        VALUES ('delete', old.id, old.stem_bn, old.stem_en, old.chapter_bn);
        INSERT INTO questions_fts(rowid, stem_bn, stem_en, chapter_bn)
        VALUES (new.id, new.stem_bn, new.stem_en, new.chapter_bn);
    END
    """,
]


def create_fts_schema(connection: Connection) -> None:
    for statement in CREATE_FTS_STATEMENTS:
        connection.execute(text(statement))


def rebuild_fts(connection: Connection) -> None:
    connection.execute(
        text("INSERT INTO questions_fts(questions_fts) VALUES ('rebuild')")
    )


def optimize_fts(connection: Connection) -> None:
    connection.execute(
        text("INSERT INTO questions_fts(questions_fts) VALUES ('optimize')")
    )
