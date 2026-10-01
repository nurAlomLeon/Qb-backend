from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config

logger = logging.getLogger("duqbank.migrations")

LOCK_TIMEOUT_SECONDS = 30.0
LOCK_STALE_SECONDS = 300.0


def _app_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _lock_path(database_url: str) -> Path:
    digest = hashlib.sha256(database_url.encode("utf-8")).hexdigest()[:12]
    name = "duqbank-migrate-{digest}.lock".format(digest=digest)
    return Path(tempfile.gettempdir()) / name


@contextmanager
def _migration_lock(
    database_url: str, timeout: float = LOCK_TIMEOUT_SECONDS
) -> Iterator[bool]:
    lock = _lock_path(database_url)
    deadline = time.monotonic() + timeout
    acquired = False

    while True:
        try:
            descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                stale = time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS
            except FileNotFoundError:
                continue
            if stale:
                try:
                    lock.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        else:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.close(descriptor)
            acquired = True
            break

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock.unlink()
            except FileNotFoundError:
                pass


def upgrade_database(database_url: str) -> None:
    app_root = _app_root()
    config = Config(str(app_root / "alembic.ini"))
    config.set_main_option("script_location", str(app_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def run_startup_migrations(database_url: str) -> bool:
    with _migration_lock(database_url) as acquired:
        if not acquired:
            logger.warning(
                "Another process is running migrations; skipping startup migration."
            )
            return False
        try:
            upgrade_database(database_url)
        except Exception:
            logger.exception(
                "Automatic database migration failed; continuing with the existing schema."
            )
            return False
        logger.info("Database schema is up to date.")
        return True
