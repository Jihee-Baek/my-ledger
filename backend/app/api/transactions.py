from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.transaction_repository import TransactionFilters
from app.schemas.transaction import (
    TransactionListOut,
    TransactionOut,
    TransactionSummaryOut,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=TransactionListOut)
def list_transactions(
    start_date: date | None = None,
    end_date: date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    category_id: int | None = None,
    uncategorized: bool = False,
    card_id: int | None = None,
    merchant: str | None = None,
    q: str | None = None,
    transaction_type: str | None = None,
    currency: str | None = None,
    include_excluded: bool = False,
    sort_by: str = Query(default="date", pattern="^(date|amount)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    filters = TransactionFilters(
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        category_id=category_id,
        uncategorized=uncategorized,
        card_id=card_id,
        merchant=merchant,
        q=q,
        transaction_type=transaction_type,
        currency=currency,
        include_excluded=include_excluded,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    items, total = transaction_service.list_transactions(db, filters, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/transactions/summary", response_model=TransactionSummaryOut)
def summarize_transactions(
    start_date: date | None = None,
    end_date: date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    category_id: int | None = None,
    uncategorized: bool = False,
    card_id: int | None = None,
    merchant: str | None = None,
    q: str | None = None,
    transaction_type: str | None = None,
    currency: str = Query(default="KRW", description="합계는 한 통화만 집계 - 통화 간 합산 금지"),
    include_excluded: bool = False,
    db: Session = Depends(get_db),
):
    """거래내역 필터와 같은 조건의 합계/비중. 목록과 같은 필터 파라미터를 받는다."""
    filters = TransactionFilters(
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        category_id=category_id,
        uncategorized=uncategorized,
        card_id=card_id,
        merchant=merchant,
        q=q,
        transaction_type=transaction_type,
        currency=currency,
        include_excluded=include_excluded,
    )
    return transaction_service.summarize_transactions(db, filters)


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = transaction_service.get_transaction(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.patch("/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int, body: TransactionUpdate, db: Session = Depends(get_db)
):
    transaction = transaction_service.update_transaction(
        db, transaction_id, category_id=body.category_id, memo=body.memo
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
