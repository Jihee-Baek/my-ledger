"""DB initialization: applies Alembic migrations, then seeds the default
category tree if it hasn't been seeded yet.

Usage:
    ./.venv/bin/python -m app.core.init_db
"""

import subprocess
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.db import SessionLocal, engine
from app.core.seed_data import CATEGORY_TREE
from app.models import Category

BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
    )


def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        print("Categories already seeded, skipping.")
        return

    for parent_name, children in CATEGORY_TREE.items():
        parent = Category(name=parent_name)
        db.add(parent)
        db.flush()  # assign parent.id before creating children
        for child_name in children:
            db.add(Category(name=child_name, parent_id=parent.id))

    db.commit()
    print(f"Seeded {len(CATEGORY_TREE)} top-level categories.")


def main() -> None:
    run_migrations()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    print(f"Database ready at: {engine.url}")


if __name__ == "__main__":
    main()
