"""add transaction direction (IN/OUT)

Revision ID: b3d1f0a2c7e5
Revises: 8ef7578a8660
Create Date: 2026-11-14 22:00:00

이체(TRANSFER)는 타입만으로 입금/출금을 알 수 없어서, 수입 <-> 이체 / 지출 <-> 이체
전환을 허용하려면 방향을 저장해야 한다. 기존 행은 raw_transactions 원본으로 채운다
(규칙은 app/services/direction.py 와 같다 - 마이그레이션이 앱 코드 변경에 흔들리지
않도록 여기서는 그대로 복사해 둔다).
"""
import json
from decimal import Decimal, InvalidOperation
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3d1f0a2c7e5"
down_revision: Union[str, Sequence[str], None] = "8ef7578a8660"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _num(value) -> Decimal:
    try:
        return Decimal(str(value).replace(",", "").strip() or "0")
    except (InvalidOperation, AttributeError):
        return Decimal(0)


def _transfer_direction(source: str, raw: dict) -> str:
    if source == "shinhan_bank":
        return "IN" if _num(raw.get("입금")) > 0 else "OUT"
    if source == "manual_bank_csv":
        return "IN" if _num(raw.get("amount")) > 0 else "OUT"
    if source == "gimpo_pay":
        return "IN" if raw.get("거래방식") == "충전" else "OUT"
    return "OUT"


def upgrade() -> None:
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("direction", sa.String(length=3), nullable=False, server_default="OUT")
        )

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE transactions SET direction = 'IN' WHERE transaction_type = 'INCOME'"))
    rows = conn.execute(
        sa.text(
            "SELECT t.id, t.source, r.raw_data FROM transactions t "
            "LEFT JOIN raw_transactions r ON r.id = t.raw_transaction_id "
            "WHERE t.transaction_type = 'TRANSFER'"
        )
    ).fetchall()
    for tx_id, source, raw_data in rows:
        try:
            raw = json.loads(raw_data) if raw_data else {}
        except ValueError:
            raw = {}
        if _transfer_direction(source, raw) == "IN":
            conn.execute(sa.text("UPDATE transactions SET direction = 'IN' WHERE id = :id"), {"id": tx_id})


def downgrade() -> None:
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_column("direction")
