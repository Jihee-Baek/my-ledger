from sqlalchemy.orm import Session

from app.models import CategoryRule


def list_rules(db: Session) -> list[CategoryRule]:
    return db.query(CategoryRule).order_by(CategoryRule.priority.desc(), CategoryRule.id).all()


def create_rule(
    db: Session, keyword: str, category_id: int, match_type: str, priority: int, enabled: bool
) -> CategoryRule:
    rule = CategoryRule(
        keyword=keyword,
        category_id=category_id,
        match_type=match_type,
        priority=priority,
        enabled=enabled,
        source="USER",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: int, **fields) -> CategoryRule | None:
    rule = db.get(CategoryRule, rule_id)
    if rule is None:
        return None
    for key, value in fields.items():
        if value is not None:
            setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int) -> bool:
    rule = db.get(CategoryRule, rule_id)
    if rule is None:
        return False
    db.delete(rule)
    db.commit()
    return True
