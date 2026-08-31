"""Seeds the SYSTEM category_rules (idempotent - safe to re-run after
adding new keywords to rules_data.py).

Usage:
    ./.venv/bin/python -m app.classifiers.seed_rules
"""

from app.classifiers.category_paths import get_or_create_category_path
from app.classifiers.rules_data import SYSTEM_RULES
from app.core.db import SessionLocal
from app.models import CategoryRule


def seed_rules(db) -> int:
    created = 0
    for category_path, keyword, priority in SYSTEM_RULES:
        category = get_or_create_category_path(db, category_path)
        exists = (
            db.query(CategoryRule)
            .filter_by(keyword=keyword, category_id=category.id, source="SYSTEM")
            .first()
        )
        if exists:
            continue
        db.add(
            CategoryRule(
                keyword=keyword,
                category_id=category.id,
                priority=priority,
                source="SYSTEM",
            )
        )
        created += 1
    db.commit()
    return created


def main() -> None:
    db = SessionLocal()
    try:
        created = seed_rules(db)
        print(f"Seeded {created} new category rules (of {len(SYSTEM_RULES)} defined).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
