"""Local MCP Server for my-ledger.

Exposes a small set of pre-defined, read-only(ish) tools backed by the
same SQLAlchemy service layer the FastAPI backend uses - no tool here
ever builds or executes arbitrary SQL, and no tool exposes full
card/account numbers (they aren't even stored - see backend/app/models).

Run directly for local testing:
    ./.venv/bin/python server.py

Registered with Claude via `claude mcp add` (see README.md).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from services.category_lookup import resolve_category_id  # noqa: E402
from services.serialize import to_jsonable  # noqa: E402
from services.transaction_view import transaction_to_dict  # noqa: E402

from mcp.server import MCPServer  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.repositories.transaction_repository import TransactionFilters  # noqa: E402
from app.services import stats_service, transaction_service  # noqa: E402

mcp = MCPServer(
    "my-ledger",
    instructions=(
        "개인 로컬 가계부 조회 도구입니다. 모든 금액 계산은 백엔드에서 수행되어 "
        "정확합니다 - 이 도구가 반환한 숫자를 임의로 재계산하지 말고 그대로 전달하세요. "
        "금액은 통화(currency)별로 분리되어 있으니 다른 통화의 금액을 서로 더하지 마세요."
    ),
)


@mcp.tool()
def get_monthly_summary(year: int, month: int, currency: str = "KRW") -> dict:
    """특정 월의 총수입/총지출/순수입과 카테고리별 지출 top 항목을 반환합니다.

    Args:
        year: 조회 연도 (예: 2026)
        month: 조회 월 (1-12)
        currency: 집계 통화 (기본 KRW). 다른 통화 지출은 결과의
            other_currencies 필드에 별도로 표시됩니다 - 절대 합산하지 마세요.
    """
    db = SessionLocal()
    try:
        return to_jsonable(stats_service.monthly_summary(db, year, month, currency))
    finally:
        db.close()


@mcp.tool()
def get_category_summary(year: int, month: int, currency: str = "KRW") -> list[dict]:
    """특정 월의 카테고리별 지출 금액과 비중(%)을 반환합니다 (지출만, 취소 제외).

    Args:
        year: 조회 연도
        month: 조회 월 (1-12)
        currency: 집계 통화 (기본 KRW)
    """
    db = SessionLocal()
    try:
        start, end = stats_service.month_bounds(year, month)
        return to_jsonable(stats_service.category_summary(db, start, end, currency))
    finally:
        db.close()


@mcp.tool()
def get_merchant_summary(year: int, month: int, months: int = 1, currency: str = "KRW", limit: int = 10) -> list[dict]:
    """지출이 많았던 가맹점 top N을 반환합니다. months=1이면 해당 월만, months>1이면
    그 달까지 거슬러 올라간 N개월 전체를 합산합니다 (예: '최근 6개월 동안 가장 많이 쓴 곳').

    Args:
        year: 기준 연도 (해당 월 또는 구간의 마지막 달)
        month: 기준 월 (1-12)
        months: 합산할 개월 수 (기본 1 = 해당 월만)
        currency: 집계 통화 (기본 KRW)
        limit: 반환할 가맹점 수 (기본 10)
    """
    db = SessionLocal()
    try:
        return to_jsonable(stats_service.merchant_summary_range(db, year, month, months, currency, limit))
    finally:
        db.close()


@mcp.tool()
def compare_month(
    base_year: int,
    base_month: int,
    target_year: int,
    target_month: int,
    currency: str = "KRW",
) -> list[dict]:
    """두 달의 카테고리별 지출을 비교해 증감액(diff)이 큰 순서로 반환합니다.

    Args:
        base_year: 비교 기준 연도 (예: 지난달)
        base_month: 비교 기준 월
        target_year: 비교 대상 연도 (예: 이번달)
        target_month: 비교 대상 월
        currency: 집계 통화 (기본 KRW)
    """
    db = SessionLocal()
    try:
        return to_jsonable(
            stats_service.compare_months(db, base_year, base_month, target_year, target_month, currency)
        )
    finally:
        db.close()


@mcp.tool()
def search_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    q: str | None = None,
    currency: str | None = None,
    limit: int = 20,
) -> dict:
    """조건에 맞는 개별 거래 내역을 검색합니다. 날짜, 카테고리, 가맹점, 키워드로 필터링합니다.

    Args:
        start_date: 검색 시작일 (YYYY-MM-DD), 생략 시 제한 없음
        end_date: 검색 종료일 (YYYY-MM-DD), 생략 시 제한 없음
        category: 카테고리명 (예: '식비', '카페'). 인식 못하면 무시하고 전체 검색합니다.
        merchant: 가맹점명 일부 (예: '스타벅스')
        q: 가맹점명 또는 적요에 대한 자유 검색어
        currency: 통화 필터 (예: 'KRW', 'USD'). 생략 시 모든 통화 포함.
        limit: 최대 반환 건수 (기본 20, 최대 100)
    """
    db = SessionLocal()
    try:
        category_id = None
        category_warning = None
        if category:
            category_id = resolve_category_id(db, category)
            if category_id is None:
                category_warning = f"'{category}' 카테고리를 찾을 수 없어 필터 없이 검색했습니다."

        filters = TransactionFilters(
            start_date=_parse_date(start_date),
            end_date=_parse_date(end_date),
            category_id=category_id,
            merchant=merchant,
            q=q,
            currency=currency,
        )
        items, total = transaction_service.list_transactions(db, filters, min(limit, 100), 0)
        result = {
            "total_matches": total,
            "returned": len(items),
            "transactions": [transaction_to_dict(db, tx) for tx in items],
        }
        if category_warning:
            result["warning"] = category_warning
        return to_jsonable(result)
    finally:
        db.close()


@mcp.tool()
def get_recurring_expenses(months: int = 3, min_months_seen: int = 2, currency: str = "KRW") -> list[dict]:
    """매달 반복적으로 결제되는 것으로 보이는 가맹점을 찾습니다 (구독료, 공과금 등).

    Args:
        months: 조회 기간 (최근 N개월, 기본 3)
        min_months_seen: 최소 몇 개월에서 발견되어야 '반복'으로 간주할지 (기본 2)
        currency: 집계 통화 (기본 KRW)
    """
    db = SessionLocal()
    try:
        return to_jsonable(stats_service.recurring_expenses(db, months, min_months_seen, currency))
    finally:
        db.close()


@mcp.tool()
def get_spending_anomalies(
    year: int,
    month: int,
    lookback_months: int = 3,
    min_change_pct: float = 30.0,
    currency: str = "KRW",
) -> dict:
    """이번 달 지출 중 평소(최근 N개월 평균)보다 많이/새롭게 늘어난 항목을 찾습니다.
    증감률은 이미 백엔드에서 계산되어 있으니 그대로 인용하고, "왜 늘었을지"/"무엇을
    줄일 수 있을지"에 대한 해석과 제안만 자연어로 덧붙이세요.

    Args:
        year: 조회 연도
        month: 조회 월 (1-12)
        lookback_months: 비교 기준이 될 과거 개월 수 (기본 3)
        min_change_pct: 이 비율(%) 이상 변한 카테고리만 표시 (기본 30)
        currency: 집계 통화 (기본 KRW)
    """
    db = SessionLocal()
    try:
        return to_jsonable(
            stats_service.spending_anomalies(db, year, month, lookback_months, min_change_pct, currency)
        )
    finally:
        db.close()


@mcp.tool()
def get_budget_status(year: int, month: int, currency: str = "KRW") -> list[dict]:
    """설정된 월 예산 대비 실제 지출과 남은 금액을 반환합니다. 예산이 없으면 빈 목록을 반환합니다.

    Args:
        year: 조회 연도
        month: 조회 월 (1-12)
        currency: 집계 통화 (기본 KRW)
    """
    db = SessionLocal()
    try:
        return to_jsonable(stats_service.budget_status(db, year, month, currency))
    finally:
        db.close()


def _parse_date(value: str | None):
    if not value:
        return None
    from datetime import date

    return date.fromisoformat(value)


if __name__ == "__main__":
    mcp.run()
