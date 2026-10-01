from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.fts import optimize_fts  # noqa: E402
from app.db.session import create_db_engine  # noqa: E402

RECOMPUTE_ATTEMPTS_SQL = """
UPDATE questions
SET analytics_attempts = (
        SELECT COUNT(*) FROM session_answers sa
        WHERE sa.question_id = questions.id AND sa.selected_index IS NOT NULL
    ),
    analytics_correct = (
        SELECT COUNT(*) FROM session_answers sa
        WHERE sa.question_id = questions.id AND sa.is_correct = 1
    )
"""

RECOMPUTE_PERCENT_SQL = """
UPDATE questions
SET analytics_percent = CASE
        WHEN analytics_attempts > 0
        THEN CAST(ROUND(analytics_correct * 100.0 / analytics_attempts) AS INTEGER)
        ELSE 0
    END
"""


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Optimize and maintain the database.")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--vacuum", action="store_true")
    parser.add_argument("--recompute-analytics", action="store_true")
    args = parser.parse_args()

    engine = create_db_engine(args.database_url or settings.database_url)

    with engine.begin() as connection:
        if args.recompute_analytics:
            connection.execute(text(RECOMPUTE_ATTEMPTS_SQL))
            connection.execute(text(RECOMPUTE_PERCENT_SQL))
            print("Recomputed per-question analytics.")
        optimize_fts(connection)
        print("FTS index optimized.")
        connection.execute(text("PRAGMA optimize"))
        print("PRAGMA optimize done.")

    if args.vacuum:
        with engine.connect() as connection:
            connection.execute(text("VACUUM"))
            print("VACUUM done.")


if __name__ == "__main__":
    main()
