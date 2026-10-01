from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _fail(name: str, exc: Exception) -> None:
    print("[FAIL] {name}: {cls}: {msg}".format(name=name, cls=exc.__class__.__name__, msg=exc))
    traceback.print_exc()


def main() -> None:
    print("Python      :", sys.version.replace("\n", " "))
    print("CWD         :", os.getcwd())
    print("App root    :", Path(__file__).resolve().parents[1])
    print("")

    try:
        from app.core.config import get_settings

        settings = get_settings()
        print("[OK]   settings load")
        print("       environment  =", settings.environment)
        print("       database_url =", settings.database_url)
        print("       cors origins =", settings.cors_origin_list)
        print("       debug        =", settings.debug)
    except Exception as exc:
        _fail("settings load", exc)
        return

    engine = None
    try:
        from app.db.session import create_db_engine, sqlite_path

        engine = create_db_engine(settings.database_url)
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        print("[OK]   database connect")

        path = sqlite_path(settings.database_url)
        if path:
            db_file = Path(path)
            resolved = db_file.resolve()
            if db_file.exists():
                print("       file         =", resolved)
                print("       writable     =", os.access(db_file, os.W_OK))
            else:
                parent = db_file.parent.resolve()
                print("       file         =", resolved, "(missing)")
                print("       parent       =", parent, "exists:", parent.exists())
                print("       parent write =", os.access(parent, os.W_OK))
    except Exception as exc:
        _fail("database connect", exc)
        print("")
        print("Hint: the directory in DUQB_DATABASE_URL must exist and be writable.")
        return

    try:
        from sqlalchemy import inspect

        tables = set(inspect(engine).get_table_names())
        print("[OK]   tables found :", len(tables))
        required = [
            "universities",
            "app_keys",
            "app_config",
            "content_meta",
            "units",
            "subjects",
            "papers",
            "questions",
            "question_options",
            "users",
            "bookmarks",
            "practice_sessions",
            "session_answers",
            "admin_users",
        ]
        missing = [name for name in required if name not in tables]
        if missing:
            print("       MISSING      :", ", ".join(missing))
            print("       -> run: python -m alembic upgrade head")
        else:
            print("       all required tables present")
    except Exception as exc:
        _fail("table inspection", exc)

    try:
        with engine.connect() as connection:
            fts_rows = connection.exec_driver_sql(
                "SELECT COUNT(*) FROM questions_fts"
            ).scalar()
        print("[OK]   questions_fts rows :", fts_rows)
    except Exception as exc:
        _fail("questions_fts", exc)
        print("       -> run: python scripts/optimize_db.py")

    try:
        with engine.connect() as connection:
            counts = {
                table: connection.exec_driver_sql(
                    "SELECT COUNT(*) FROM {table}".format(table=table)
                ).scalar()
                for table in ("universities", "units", "papers", "questions", "admin_users", "app_keys")
            }
        print("[OK]   content counts :", counts)
        if counts["universities"] == 0:
            print("       -> run: python scripts/seed_demo.py --reset --admin-username admin --admin-password '...'")
        if counts["admin_users"] == 0:
            print("       -> run: python scripts/create_admin.py --username admin --password '...'")
        if counts["app_keys"] == 0:
            print("       -> generate an app key in /admin/keygen after creating an admin")
    except Exception as exc:
        _fail("content counts", exc)

    try:
        from app.main import app

        print("[OK]   FastAPI app loads :", len(app.routes), "routes")
    except Exception as exc:
        _fail("FastAPI app import", exc)

    try:
        import passenger_wsgi

        print("[OK]   passenger_wsgi loads :", type(passenger_wsgi.application).__name__)
    except Exception as exc:
        _fail("passenger_wsgi import", exc)

    print("")
    print("Done. If everything above is OK but the site still returns 500,")
    print("check the Passenger log: tail -n 60 stderr.log")


if __name__ == "__main__":
    main()
