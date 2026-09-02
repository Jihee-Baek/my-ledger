"""CSV/Excel import pipeline:

    file -> Adapter.parse() -> raw_transactions (verbatim) -> normalize
    -> dedupe by fingerprint -> transactions

Usage:
    ./.venv/bin/python -m app.services.import_service <file_path> [<file_path> ...]
"""

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.classifiers.rule_classifier import classify_transaction
from app.core.db import SessionLocal
from app.importers import REGISTRY, ParsedTransaction
from app.importers.normalize import mark_cancelled_pairs
from app.models import ImportBatch, RawTransaction, Transaction
from app.services.fingerprint import build_fingerprint
from app.services.reference_data import get_or_create_card, get_or_create_default_owner


class NoMatchingImporterError(Exception):
    pass


@dataclass
class ImportResult:
    source: str
    file_name: str
    batch_id: int | None
    total: int
    imported: int
    duplicates: int
    classified: int
    unclassified: int


def _find_importer(file_path: Path):
    for importer in REGISTRY:
        if importer.can_handle(file_path):
            return importer
    raise NoMatchingImporterError(
        f"No importer recognizes this file's format: {file_path.name}"
    )


def _row_to_json(row: dict) -> str:
    return json.dumps(row, ensure_ascii=False, default=str)


def import_file(file_path: Path, db: Session, dry_run: bool = False) -> ImportResult:
    """dry_run=True runs the full pipeline (parse, dedup check,
    classification) to compute accurate preview counts, then rolls
    back instead of committing - nothing is persisted, including any
    Merchant rows classify_transaction would otherwise create."""

    importer = _find_importer(file_path)
    parsed_rows: list[ParsedTransaction] = importer.parse(file_path)
    mark_cancelled_pairs(parsed_rows)

    batch = ImportBatch(
        source=importer.source,
        file_name=file_path.name,
        row_count=len(parsed_rows),
        status="SUCCESS",
    )
    db.add(batch)
    db.flush()

    owner = get_or_create_default_owner(db)

    imported = 0
    duplicates = 0
    classified = 0
    unclassified = 0
    for parsed in parsed_rows:
        fingerprint = build_fingerprint(parsed, importer.source)
        if db.query(Transaction.id).filter_by(fingerprint=fingerprint).first():
            duplicates += 1
            continue

        raw = RawTransaction(
            import_batch_id=batch.id,
            source=importer.source,
            raw_data=_row_to_json(parsed.raw_row),
            row_hash=fingerprint,
        )
        db.add(raw)
        db.flush()

        card = get_or_create_card(db, owner, parsed.card_institution, parsed.card_number_masked)

        transaction = Transaction(
            raw_transaction_id=raw.id,
            transaction_date=parsed.transaction_date,
            transaction_time=parsed.transaction_time,
            transaction_type=parsed.transaction_type,
            amount=Decimal(parsed.amount),
            currency=parsed.currency,
            merchant_raw=parsed.merchant_raw,
            description=parsed.description,
            card_id=card.id,
            is_excluded=parsed.is_excluded,
            source=importer.source,
            source_transaction_id=parsed.source_transaction_id,
            fingerprint=fingerprint,
        )
        classify_transaction(db, transaction)
        db.add(transaction)
        imported += 1
        if transaction.category_id is not None:
            classified += 1
        else:
            unclassified += 1

    if dry_run:
        db.rollback()
        batch_id = None
    else:
        db.commit()
        batch_id = batch.id

    return ImportResult(
        source=importer.source,
        file_name=file_path.name,
        batch_id=batch_id,
        total=len(parsed_rows),
        imported=imported,
        duplicates=duplicates,
        classified=classified,
        unclassified=unclassified,
    )


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    db = SessionLocal()
    try:
        for arg in sys.argv[1:]:
            result = import_file(Path(arg), db)
            print(
                f"[{result.source}] {result.file_name}: 전체 {result.total}건 / "
                f"{result.imported}건 신규 저장({result.classified}건 분류, {result.unclassified}건 미분류) / "
                f"{result.duplicates}건 중복 건너뜀 (batch_id={result.batch_id})"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
