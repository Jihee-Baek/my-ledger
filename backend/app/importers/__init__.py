from app.importers.base import ParsedTransaction, TransactionImporter
from app.importers.gimpo_pay import GimpoPayImporter
from app.importers.hyundai import HyundaiCardImporter
from app.importers.manual_csv import ManualBankCsvImporter
from app.importers.samsung import SamsungCardImporter
from app.importers.shinhan import ShinhanCardImporter
from app.importers.shinhan_bank import ShinhanBankImporter
from app.importers.shinhan_transit import ShinhanTransitImporter

REGISTRY: list[TransactionImporter] = [
    SamsungCardImporter(),
    ShinhanCardImporter(),
    ShinhanTransitImporter(),
    ShinhanBankImporter(),
    HyundaiCardImporter(),
    ManualBankCsvImporter(),
    GimpoPayImporter(),
]

__all__ = ["ParsedTransaction", "TransactionImporter", "REGISTRY"]
