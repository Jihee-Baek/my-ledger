from app.importers.base import ParsedTransaction, TransactionImporter
from app.importers.hyundai import HyundaiCardImporter
from app.importers.samsung import SamsungCardImporter
from app.importers.shinhan import ShinhanCardImporter

REGISTRY: list[TransactionImporter] = [
    SamsungCardImporter(),
    ShinhanCardImporter(),
    HyundaiCardImporter(),
]

__all__ = ["ParsedTransaction", "TransactionImporter", "REGISTRY"]
