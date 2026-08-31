"""Import every model so Base.metadata is fully populated for Alembic
autogenerate and for Base.metadata.create_all()."""

from app.models.account import Account
from app.models.card import Card
from app.models.category import Category
from app.models.category_rule import CategoryRule
from app.models.import_batch import ImportBatch
from app.models.merchant import Merchant
from app.models.monthly_budget import MonthlyBudget
from app.models.owner import Owner
from app.models.raw_transaction import RawTransaction
from app.models.transaction import Transaction

__all__ = [
    "Account",
    "Card",
    "Category",
    "CategoryRule",
    "ImportBatch",
    "Merchant",
    "MonthlyBudget",
    "Owner",
    "RawTransaction",
    "Transaction",
]
