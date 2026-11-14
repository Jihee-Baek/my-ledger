from sqlalchemy.orm import Session

from app.classifiers.rule_classifier import classify_transaction, set_user_category
from app.models import Transaction
from app.services.direction import ALLOWED_TYPES
from app.repositories.transaction_repository import (
    TransactionFilters,
    get_by_id,
    search,
)


def list_transactions(
    db: Session, filters: TransactionFilters, limit: int, offset: int
) -> tuple[list[Transaction], int]:
    return search(db, filters, limit, offset)


def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return get_by_id(db, transaction_id)


_TYPE_LABEL = {"INCOME": "수입", "EXPENSE": "지출", "TRANSFER": "이체"}


def change_transaction_type(db: Session, transaction: Transaction, new_type: str) -> None:
    """수입/지출 <-> 이체 전환. 들어온 돈은 수입·이체, 나간 돈은 지출·이체 중에서만 고를 수 있다.
    이체로 바꾸면 카테고리를 비우고(이체는 분류 대상이 아님), 수입/지출로 되돌리면
    가맹점 학습값·규칙으로 다시 분류한다. 가맹점 학습값은 건드리지 않는다."""
    if new_type == transaction.transaction_type:
        return
    allowed = ALLOWED_TYPES.get(transaction.direction, set())
    if new_type not in allowed:
        kind = "입금" if transaction.direction == "IN" else "출금"
        options = "/".join(_TYPE_LABEL[t] for t in sorted(allowed))
        raise ValueError(f"{kind} 거래는 {options}(으)로만 바꿀 수 있습니다")

    transaction.transaction_type = new_type
    transaction.category_id = None
    transaction.category_confirmed = False
    if new_type != "TRANSFER":
        classify_transaction(db, transaction)


def update_transaction(
    db: Session,
    transaction_id: int,
    category_id: int | None,
    memo: str | None,
    transaction_type: str | None = None,
) -> Transaction | None:
    transaction = get_by_id(db, transaction_id)
    if transaction is None:
        return None

    if transaction_type is not None:
        change_transaction_type(db, transaction, transaction_type)
    # 이체는 분류 대상이 아니므로 같이 넘어온 category_id는 무시한다
    if category_id is not None and transaction.transaction_type != "TRANSFER":
        set_user_category(db, transaction, category_id)
    if memo is not None:
        transaction.memo = memo

    db.commit()
    db.refresh(transaction)
    return transaction


def summarize_transactions(db: Session, filters: TransactionFilters) -> dict:
    """Totals for whatever the 거래내역 filter panel currently shows, plus a
    breakdown one level below the selected category (no category -> 상위
    카테고리별, 상위 선택 -> 하위별, 하위 선택 -> 가맹점별) so the share of
    each part is visible. All arithmetic happens here, never in the UI."""
    from decimal import Decimal

    from app.models import Category
    from app.repositories.transaction_repository import (
        expense_by_category,
        expense_by_merchant,
        period_expense_total,
        totals_by_type,
    )

    by_type = totals_by_type(db, filters)
    expense_count, total_expense = by_type.get("EXPENSE", (0, Decimal(0)))
    income_count, total_income = by_type.get("INCOME", (0, Decimal(0)))
    transfer_count, total_transfer = by_type.get("TRANSFER", (0, Decimal(0)))

    period_total = period_expense_total(db, filters)
    share = float(total_expense) / float(period_total) * 100 if period_total else None

    categories = {c.id: c for c in db.query(Category).all()}
    selected = categories.get(filters.category_id) if filters.category_id else None

    def pct(amount: Decimal) -> float:
        return round(float(amount) / float(total_expense) * 100, 1) if total_expense else 0.0

    if selected is not None and selected.parent_id is not None:
        kind = "merchant"
        rows = [(m or "(알 수 없음)", amt) for m, amt in expense_by_merchant(db, filters, limit=10)]
    else:
        kind = "child" if selected is not None else "parent"
        buckets: dict[str, Decimal] = {}
        for category_id, amount in expense_by_category(db, filters):
            category = categories.get(category_id) if category_id else None
            if category is None:
                label = "미분류"
            elif kind == "child":
                label = category.name if category.id != selected.id else f"{selected.name} (직접 분류)"
            else:
                top = categories.get(category.parent_id) if category.parent_id else category
                label = top.name
            buckets[label] = buckets.get(label, Decimal(0)) + amount
        rows = sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)

    return {
        "currency": filters.currency,
        "count": expense_count + income_count + transfer_count,
        "expense_count": expense_count,
        "income_count": income_count,
        "transfer_count": transfer_count,
        "total_expense": total_expense,
        "total_income": total_income,
        "total_transfer": total_transfer,
        "period_expense_total": period_total,
        "expense_share_pct": round(share, 1) if share is not None else None,
        "breakdown_kind": kind,
        "breakdown": [
            {"category": label, "amount": amount, "percentage": pct(amount)} for label, amount in rows
        ],
    }
