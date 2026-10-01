from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models.admin import AdminUser  # noqa: E402
from app.models.university import University  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", default="super_admin", choices=["super_admin", "tenant_admin"])
    parser.add_argument("--university-slug", default=None)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    settings = get_settings()
    engine = create_db_engine(args.database_url or settings.database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        university_id = None
        if args.university_slug:
            university = db.execute(
                select(University).where(University.slug == args.university_slug)
            ).scalar_one_or_none()
            if university is None:
                raise SystemExit("University '{slug}' not found.".format(slug=args.university_slug))
            university_id = university.id

        admin = db.execute(
            select(AdminUser).where(AdminUser.username == args.username)
        ).scalar_one_or_none()

        if admin is None:
            admin = AdminUser(
                username=args.username,
                password_hash=hash_password(args.password),
                role=args.role,
                university_id=university_id,
            )
            db.add(admin)
            print("Created admin '{user}'.".format(user=args.username))
        else:
            admin.password_hash = hash_password(args.password)
            admin.role = args.role
            admin.university_id = university_id
            admin.is_active = True
            print("Updated admin '{user}'.".format(user=args.username))

        db.commit()


if __name__ == "__main__":
    main()
