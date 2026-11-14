from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.fixed_expense import (
    FixedExpenseCreate,
    FixedExpenseOut,
    FixedExpenseOverview,
    FixedExpenseUpdate,
)
from app.services import fixed_expense_service

router = APIRouter(tags=["fixed-expenses"])


@router.get("/fixed-expenses/overview", response_model=FixedExpenseOverview)
def fixed_expense_overview(year: int, month: int, db: Session = Depends(get_db)):
    """등록된 고정 지출 항목별 최근 6개월 납부 현황 + 등록 후보."""
    return fixed_expense_service.overview(db, year, month)


@router.post("/fixed-expenses", response_model=FixedExpenseOut, status_code=201)
def create_fixed_expense(body: FixedExpenseCreate, db: Session = Depends(get_db)):
    return fixed_expense_service.create(db, body.model_dump())


@router.patch("/fixed-expenses/{item_id}", response_model=FixedExpenseOut)
def update_fixed_expense(item_id: int, body: FixedExpenseUpdate, db: Session = Depends(get_db)):
    item = fixed_expense_service.update(db, item_id, body.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Fixed expense not found")
    return item


@router.delete("/fixed-expenses/{item_id}", status_code=204)
def delete_fixed_expense(item_id: int, db: Session = Depends(get_db)):
    if not fixed_expense_service.delete(db, item_id):
        raise HTTPException(status_code=404, detail="Fixed expense not found")
