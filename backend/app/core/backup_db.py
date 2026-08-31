"""Manual SQLite backup/restore.

Usage:
    ./.venv/bin/python -m app.core.backup_db backup
    ./.venv/bin/python -m app.core.backup_db restore <backups/ledger_YYYYMMDD_HHMMSS.db>
"""

import shutil
import sqlite3
import sys
from datetime import datetime

from app.core.config import settings


def backup() -> None:
    db_path = settings.database_path
    if not db_path.exists():
        raise SystemExit(f"No database found at {db_path}")

    settings.backups_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = settings.backups_path / f"ledger_{timestamp}.db"

    # Use SQLite's own backup API rather than a raw file copy, so an
    # in-progress write elsewhere can't produce a corrupt snapshot.
    source_conn = sqlite3.connect(db_path)
    dest_conn = sqlite3.connect(dest)
    with dest_conn:
        source_conn.backup(dest_conn)
    source_conn.close()
    dest_conn.close()

    print(f"Backed up {db_path} -> {dest}")


def restore(backup_file: str) -> None:
    from pathlib import Path

    backup_path = Path(backup_file)
    if not backup_path.exists():
        raise SystemExit(f"Backup file not found: {backup_path}")

    db_path = settings.database_path
    if db_path.exists():
        safety_copy = db_path.with_suffix(".db.before-restore")
        shutil.copy2(db_path, safety_copy)
        print(f"Existing DB saved to {safety_copy} before restore.")

    shutil.copy2(backup_path, db_path)
    print(f"Restored {backup_path} -> {db_path}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("backup", "restore"):
        raise SystemExit(__doc__)

    if sys.argv[1] == "backup":
        backup()
    else:
        if len(sys.argv) != 3:
            raise SystemExit("Usage: python -m app.core.backup_db restore <path-to-backup.db>")
        restore(sys.argv[2])


if __name__ == "__main__":
    main()
