from sqlalchemy.orm import Session

from app.models import Category


def resolve_category_id(db: Session, name: str) -> int | None:
    """Case-sensitive exact match against any category name (top-level
    or sub-category), e.g. '식비' or '카페'. Returns None if unrecognized -
    callers should fall back to searching without a category filter and
    surface a warning, rather than silently matching the wrong thing."""
    category = db.query(Category).filter_by(name=name).first()
    return category.id if category else None
