"""고정 지출: 등록된 항목별로 최근 N개월 지출을 묶어 한눈에 보여주고, 아직 등록되지 않은
'매달 비슷하게 나가는' 지출을 후보로 추천한다. 금액 계산은 전부 여기서 한다 (화면은 표시만).
"""

import re
import statistics
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, Category, FixedExpense, Transaction
from app.services.stats_service import _trailing_year_months, month_bounds

WINDOW_MONTHS = 6
# 후보 추천에서 뺄 상위 카테고리 - 자주 가도 '고정' 지출은 아닌 것들
_CANDIDATE_EXCLUDED_ROOTS = {"식비", "쇼핑", "여행", "문화/여가"}


def collapse(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_merchant(name: str | None) -> str:
    """달마다 바뀌는 꼬리표를 떼어낸 가맹점 키워드.
    'DB손02609'->'DB손', '청약19001(65)'->'청약', '023.이화진'->'이화진',
    'KT 통신요금 자동납부 09월 - 575100'->'KT 통신요금 자동납부', '신한Life09-033'->'신한Life'"""
    s = collapse(name)
    s = re.sub(r"^\d+\.", "", s)
    s = re.sub(r"\d{1,2}월", "", s)
    s = re.sub(r"\(\d+\)$", "", s.strip())
    s = re.sub(r"[\s\d\-]+$", "", s)
    return collapse(s)


def _matches(item: FixedExpense, tx: Transaction) -> bool:
    if item.keyword.lower() not in collapse(tx.merchant_raw).lower():
        return False
    if item.card_id is not None and tx.card_id != item.card_id:
        return False
    if item.amount is not None and abs(Decimal(tx.amount) - Decimal(item.amount)) > Decimal("0.5"):
        return False
    return True


def _specificity(item: FixedExpense) -> tuple:
    # 조건이 많은 항목이 먼저 거래를 가져가야 'DB손 76,290' 이 'DB손' 에 먹히지 않는다
    return (item.amount is None, item.card_id is None, -len(item.keyword), item.id)


def _ym(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _card_labels(db: Session) -> dict[int, str]:
    return {c.id: c.card_name or collapse(f"{c.institution} {c.card_number_masked or ''}") for c in db.query(Card).all()}


def _window_expenses(db: Session, start: date, end: date) -> list[Transaction]:
    return list(
        db.scalars(
            select(Transaction)
            .where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                Transaction.transaction_type == "EXPENSE",
                Transaction.is_excluded.is_(False),
                Transaction.currency == "KRW",
                Transaction.merchant_raw.is_not(None),
            )
            .order_by(Transaction.transaction_date, Transaction.transaction_time, Transaction.id)
        )
    )


def overview(db: Session, year: int, month: int, today: date | None = None) -> dict:
    today = today or date.today()
    months = _trailing_year_months(year, month, WINDOW_MONTHS)
    month_keys = [f"{y:04d}-{m:02d}" for y, m in months]
    window_start, _ = month_bounds(*months[0])
    _, window_end = month_bounds(year, month)
    selected_key = month_keys[-1]

    categories = {c.id: c for c in db.query(Category).all()}
    card_labels = _card_labels(db)
    txs = _window_expenses(db, window_start, window_end)

    items = sorted(db.query(FixedExpense).filter_by(is_active=True).all(), key=_specificity)
    claimed: set[int] = set()
    rows = []
    for item in items:
        matched = [tx for tx in txs if tx.id not in claimed and _matches(item, tx)]
        claimed.update(tx.id for tx in matched)

        by_month: dict[str, Decimal] = defaultdict(Decimal)
        count_by_month: dict[str, int] = defaultdict(int)
        for tx in matched:
            by_month[_ym(tx.transaction_date)] += Decimal(tx.amount)
            count_by_month[_ym(tx.transaction_date)] += 1

        paid_months = [k for k in month_keys if by_month.get(k)]
        last_tx = matched[-1] if matched else None
        latest_amount = by_month[paid_months[-1]] if paid_months else (Decimal(item.amount) if item.amount else Decimal(0))
        average = (
            sum((by_month[k] for k in paid_months), Decimal(0)) / len(paid_months) if paid_months else Decimal(0)
        )
        pay_day = int(statistics.median(tx.transaction_date.day for tx in matched)) if matched else None

        category = categories.get(item.category_id) if item.category_id else None
        if category is None and last_tx is not None and last_tx.category_id:
            category = categories.get(last_tx.category_id)
        root = categories.get(category.parent_id) if category and category.parent_id else category

        selected_amount = by_month.get(selected_key, Decimal(0))
        if selected_amount:
            status = "paid"
        elif (year, month) > (today.year, today.month):
            status = "upcoming"
        elif (year, month) == (today.year, today.month):
            status = "upcoming" if pay_day is None or today.day <= pay_day else "unconfirmed"
        else:
            status = "missing"

        card_id = item.card_id or (last_tx.card_id if last_tx else None)
        rows.append(
            {
                "id": item.id,
                "name": item.name,
                "keyword": item.keyword,
                "amount_filter": item.amount,
                "card_id": item.card_id,
                "card_label": card_labels.get(card_id) if card_id else None,
                "category": category.name if category else None,
                "category_group": root.name if root else "기타",
                "memo": item.memo,
                "pay_day": pay_day,
                "latest_amount": latest_amount,
                "average_amount": average.quantize(Decimal("1")),
                "months_paid": len(paid_months),
                "last_paid_date": last_tx.transaction_date if last_tx else None,
                "selected_month_amount": selected_amount,
                "status": status,
                "monthly": [
                    {"month": k, "amount": by_month.get(k, Decimal(0)), "count": count_by_month.get(k, 0)}
                    for k in month_keys
                ],
            }
        )

    rows.sort(key=lambda r: (r["category_group"], r["pay_day"] or 99, r["name"]))

    monthly_totals = [
        {"month": k, "amount": sum((r["monthly"][i]["amount"] for r in rows), Decimal(0))}
        for i, k in enumerate(month_keys)
    ]
    expected_total = sum((r["latest_amount"] for r in rows), Decimal(0))
    paid_total = sum((r["selected_month_amount"] for r in rows), Decimal(0))
    remaining_total = sum((r["latest_amount"] for r in rows if r["status"] != "paid"), Decimal(0))

    group_totals: dict[str, Decimal] = defaultdict(Decimal)
    for r in rows:
        group_totals[r["category_group"]] += r["latest_amount"]

    return {
        "year": year,
        "month": month,
        "months": month_keys,
        "items": rows,
        "monthly_totals": monthly_totals,
        "expected_monthly_total": expected_total,
        "selected_paid_total": paid_total,
        "selected_remaining_total": remaining_total,
        "paid_count": sum(1 for r in rows if r["status"] == "paid"),
        "item_count": len(rows),
        "group_totals": [
            {
                "group": g,
                "amount": a,
                "percentage": round(float(a) / float(expected_total) * 100, 1) if expected_total else 0.0,
            }
            for g, a in sorted(group_totals.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "candidates": candidates(db, txs, items, categories, card_labels, month_keys),
    }


def candidates(db, txs, items, categories, card_labels, month_keys) -> list[dict]:
    """등록 안 된 지출 중 '최근 6개월 중 3개월 이상, 한 달에 한 번꼴, 금액이 거의 일정'한 것.
    금액이 들쭉날쭉해도 같은 금액이 3개월 이상 반복되면(같은 이름의 보험 두 건 등) 그 금액으로 추천."""

    def root_name(category_id):
        c = categories.get(category_id) if category_id else None
        if c is None:
            return None
        return (categories.get(c.parent_id) if c.parent_id else c).name

    groups: dict[tuple[str, int | None], list[Transaction]] = defaultdict(list)
    for tx in txs:
        if any(_matches(item, tx) for item in items):
            continue
        if root_name(tx.category_id) in _CANDIDATE_EXCLUDED_ROOTS:
            continue
        key = normalize_merchant(tx.merchant_raw)
        if len(key) < 2:
            continue
        groups[(key, tx.card_id)].append(tx)

    out = []
    for (keyword, card_id), group in groups.items():
        by_month: dict[str, Decimal] = defaultdict(Decimal)
        for tx in group:
            by_month[_ym(tx.transaction_date)] += Decimal(tx.amount)
        if len(by_month) < 3:
            continue
        totals = [float(v) for v in by_month.values()]
        mean = statistics.mean(totals)
        cv = statistics.pstdev(totals) / mean if mean else 1
        per_month = len(group) / len(by_month)
        last = group[-1]
        base = {
            "keyword": keyword,
            "card_id": card_id,
            "card_label": card_labels.get(card_id) if card_id else None,
            "category_id": last.category_id,
            "category": categories[last.category_id].name if last.category_id in categories else None,
            "pay_day": int(statistics.median(tx.transaction_date.day for tx in group)),
        }
        if per_month <= 1.5 and cv <= 0.35:
            out.append(
                {**base, "name": keyword, "amount_filter": None, "months_seen": len(by_month),
                 "typical_amount": Decimal(str(round(mean))), "last_amount": by_month[max(by_month)]}
            )
            continue
        months_by_amount: dict[Decimal, set[str]] = defaultdict(set)
        for tx in group:
            months_by_amount[Decimal(tx.amount)].add(_ym(tx.transaction_date))
        for amount, seen in months_by_amount.items():
            if len(seen) >= 3 and amount > 0:
                out.append(
                    {**base, "name": f"{keyword} {int(amount):,}원", "amount_filter": amount,
                     "months_seen": len(seen), "typical_amount": amount, "last_amount": amount}
                )
    out.sort(key=lambda c: (-c["months_seen"], -c["typical_amount"]))
    return out


def create(db: Session, data: dict) -> FixedExpense:
    item = FixedExpense(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update(db: Session, item_id: int, data: dict) -> FixedExpense | None:
    item = db.get(FixedExpense, item_id)
    if item is None:
        return None
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


def delete(db: Session, item_id: int) -> bool:
    item = db.get(FixedExpense, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True
