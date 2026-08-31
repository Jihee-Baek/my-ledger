from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category_rule import CategoryRuleCreate, CategoryRuleOut, CategoryRuleUpdate
from app.services import category_rule_service

router = APIRouter(tags=["category-rules"])


@router.get("/category-rules", response_model=list[CategoryRuleOut])
def list_category_rules(db: Session = Depends(get_db)):
    return category_rule_service.list_rules(db)


@router.post("/category-rules", response_model=CategoryRuleOut)
def create_category_rule(body: CategoryRuleCreate, db: Session = Depends(get_db)):
    return category_rule_service.create_rule(
        db, body.keyword, body.category_id, body.match_type, body.priority, body.enabled
    )


@router.patch("/category-rules/{rule_id}", response_model=CategoryRuleOut)
def update_category_rule(rule_id: int, body: CategoryRuleUpdate, db: Session = Depends(get_db)):
    rule = category_rule_service.update_rule(db, rule_id, **body.model_dump(exclude_unset=True))
    if rule is None:
        raise HTTPException(status_code=404, detail="Category rule not found")
    return rule


@router.delete("/category-rules/{rule_id}", status_code=204)
def delete_category_rule(rule_id: int, db: Session = Depends(get_db)):
    if not category_rule_service.delete_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Category rule not found")
