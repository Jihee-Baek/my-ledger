from sqlalchemy.orm import Session

from app.models import Category


def get_category_tree(db: Session) -> list[Category]:
    """Returns only top-level categories; each has .children populated
    via the SQLAlchemy relationship for the API layer to serialize."""
    return db.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.id).all()
