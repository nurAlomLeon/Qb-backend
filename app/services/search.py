from __future__ import annotations

import re
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.content import SearchResultOut

_WORD_RE = re.compile(r"[\w\u0980-\u09FF]+", re.UNICODE)

_SEARCH_SQL = text(
    """
    SELECT
        q.id AS question_id,
        q.paper_id AS paper_id,
        q.serial AS serial,
        q.stem_bn AS stem_bn,
        s.code AS subject_code,
        snippet(questions_fts, 0, '', '', '…', 10) AS snippet
    FROM questions_fts
    JOIN questions q ON q.id = questions_fts.rowid
    JOIN subjects s ON s.id = q.subject_id
    WHERE questions_fts MATCH :match
      AND q.university_id = :university_id
      AND q.is_published = 1
    ORDER BY bm25(questions_fts, 1.0, 0.4, 0.2)
    LIMIT :limit
    """
)


def search_questions(
    db: Session, university_id: int, query: str, limit: int = 20
) -> List[SearchResultOut]:
    tokens = _WORD_RE.findall(query or "")
    if not tokens:
        return []
    match = " ".join('"{token}"*'.format(token=token) for token in tokens)
    rows = db.execute(
        _SEARCH_SQL,
        {"match": match, "university_id": university_id, "limit": limit},
    ).mappings().all()
    return [SearchResultOut(**row) for row in rows]
