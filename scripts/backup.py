from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.session import sqlite_path  # noqa: E402


def backup(source_path: Path, out_dir: Path, keep: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_path = out_dir / "{stem}-{stamp}.db".format(stem=source_path.stem, stamp=stamp)

    source = sqlite3.connect(str(source_path))
    try:
        target = sqlite3.connect(str(target_path))
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()

    backups = sorted(out_dir.glob("{stem}-*.db".format(stem=source_path.stem)))
    for old in backups[:-keep] if keep > 0 else []:
        old.unlink()

    return target_path


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Backup the SQLite database.")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--out", default="backups")
    parser.add_argument("--keep", type=int, default=14)
    args = parser.parse_args()

    database_url = args.database_url or settings.database_url
    path = sqlite_path(database_url)
    if not path:
        raise SystemExit("Only SQLite databases are supported by this script.")
    source_path = Path(path)
    if not source_path.exists():
        raise SystemExit("Database file not found: {path}".format(path=source_path))

    target = backup(source_path, Path(args.out), args.keep)
    print("Backup written to {target}".format(target=target))


if __name__ == "__main__":
    main()
