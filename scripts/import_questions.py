from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models.content import Paper  # noqa: E402
from app.services.importing import import_rows, parse_upload  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk import questions into a paper.")
    parser.add_argument("--paper-id", type=int, required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--subject-code", default="")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit("File not found: {path}".format(path=path))

    settings = get_settings()
    engine = create_db_engine(args.database_url or settings.database_url)
    session_factory = create_session_factory(engine)

    rows = parse_upload(path.name, path.read_bytes())

    with session_factory() as db:
        paper = db.get(Paper, args.paper_id)
        if paper is None:
            raise SystemExit("Paper {id} not found.".format(id=args.paper_id))

        report = import_rows(db, paper, rows, args.subject_code)

    print(
        "Created: {created}  Updated: {updated}  Skipped: {skipped}".format(
            created=report["created"],
            updated=report["updated"],
            skipped=report["skipped"],
        )
    )
    for message in report["errors"][:20]:
        print(" - {message}".format(message=message))


if __name__ == "__main__":
    main()
