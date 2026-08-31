from sqlalchemy.orm import Session

from app.models import Category


def get_category_by_path(db: Session, path: tuple[str, ...]) -> Category | None:
    """Resolves e.g. ('식비', '카페') by walking parent -> child."""
    parent_id = None
    category = None
    for name in path:
        category = db.query(Category).filter_by(name=name, parent_id=parent_id).first()
        if category is None:
            return None
        parent_id = category.id
    return category


def get_or_create_category_path(db: Session, path: tuple[str, ...]) -> Category:
    parent_id = None
    category = None
    for name in path:
        category = db.query(Category).filter_by(name=name, parent_id=parent_id).first()
        if category is None:
            category = Category(name=name, parent_id=parent_id)
            db.add(category)
            db.flush()
        parent_id = category.id
    return category
