"""Delete seeded demo questions so only scraped content remains.

Seed data created by scripts/seed_demo.py has no `source` value, while scraped
questions carry source="aapathshala". This script removes the demo questions
(and optionally the papers that end up empty), leaving units/subjects intact.

Examples:
  python scripts/purge_demo_content.py --university du --unit ক --drop-empty-papers
  python scripts/purge_demo_content.py --university du --paper-id 3 --yes
  python scripts/purge_demo_content.py --university du --yes          # whole university
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models.content import Paper, Question, Unit  # noqa: E402
from app.models.university import ContentMeta, University  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge seeded demo questions.")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--university", required=True, help="university slug, e.g. du")
    parser.add_argument("--unit", default=None, help="unit letter, e.g. ক (optional)")
    parser.add_argument("--paper-id", type=int, default=None, help="single paper (optional)")
    parser.add_argument(
        "--drop-empty-papers",
        action="store_true",
        help="delete papers that have no questions left after the purge",
    )
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_db_engine(args.database_url or settings.database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        university = db.execute(
            select(University).where(University.slug == args.university)
        ).scalar_one_or_none()
        if university is None:
            raise SystemExit("University '{slug}' not found.".format(slug=args.university))

        paper_scope = [Paper.university_id == university.id]
        question_filters = [
            Question.university_id == university.id,
            Question.source.is_(None),
        ]

        if args.unit:
            unit = db.execute(
                select(Unit).where(
                    Unit.university_id == university.id,
                    Unit.letter == args.unit,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise SystemExit("Unit '{letter}' not found.".format(letter=args.unit))
            paper_scope.append(Paper.unit_id == unit.id)
            question_filters.append(
                Question.paper_id.in_(
                    select(Paper.id).where(Paper.unit_id == unit.id)
                )
            )

        if args.paper_id:
            paper = db.get(Paper, args.paper_id)
            if paper is None or paper.university_id != university.id:
                raise SystemExit("Paper {id} not found.".format(id=args.paper_id))
            paper_scope = [Paper.id == args.paper_id]
            question_filters = [
                Question.paper_id == args.paper_id,
                Question.source.is_(None),
            ]

        matched = (
            db.scalar(select(func.count(Question.id)).where(*question_filters)) or 0
        )
        print("Seeded (demo) questions matched: {n}".format(n=matched))

        if matched == 0 and not args.drop_empty_papers:
            print("Nothing to do.")
            return

        if not args.yes:
            answer = input("Delete them? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted.")
                return

        if matched:
            db.execute(delete(Question).where(*question_filters))
            db.commit()
            print("Deleted {n} demo questions.".format(n=matched))

        if args.drop_empty_papers:
            papers = db.execute(select(Paper).where(*paper_scope)).scalars().all()
            removed = 0
            kept = 0
            for paper in papers:
                remaining = (
                    db.scalar(
                        select(func.count(Question.id)).where(
                            Question.paper_id == paper.id
                        )
                    )
                    or 0
                )
                if remaining == 0:
                    db.delete(paper)
                    removed += 1
                else:
                    paper.question_count = remaining
                    kept += 1
            meta = db.execute(
                select(ContentMeta).where(
                    ContentMeta.university_id == university.id
                )
            ).scalar_one_or_none()
            if meta is not None:
                meta.content_version += 1
            db.commit()
            print(
                "Dropped {removed} empty papers, kept {kept} with scraped questions.".format(
                    removed=removed, kept=kept
                )
            )

        remaining_questions = (
            db.scalar(
                select(func.count(Question.id)).where(
                    Question.university_id == university.id
                )
            )
            or 0
        )
        print(
            "University '{slug}' now has {n} questions.".format(
                slug=university.slug, n=remaining_questions
            )
        )


if __name__ == "__main__":
    main()
