"""
Domain Application Service for Finances.
Contains financial entries processing and summary aggregations.
"""

from typing import List, Optional, Dict
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.finances.interfaces import IFinanceRepository

class FinancesService:
    def __init__(self, repo: IFinanceRepository):
        self.repo = repo

    def list_entries(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Finance]:
        return self.repo.list_entries(start_date=start_date, end_date=end_date)

    def create_entry(self, finance_in: schemas.FinanceCreate) -> models.Finance:
        return self.repo.create_entry(finance_in)

    def bulk_create_entries(self, finance_ins: List[schemas.FinanceCreate]) -> List[models.Finance]:
        return self.repo.bulk_create_entries(finance_ins)

    def delete_entry(self, finance_id: int) -> bool:
        success = self.repo.delete_entry(finance_id)
        if not success:
            raise EntityNotFoundException(entity_name="Finance", identifier=str(finance_id))
        return True

    def calculate_totals(self, entries: List[models.Finance]) -> Dict[str, float]:
        """Calculate total income, expenses, and savings from entries."""
        income = sum(e.amount for e in entries if getattr(e, "transaction_type", getattr(e, "type", "")).lower() == "income")
        expense = sum(e.amount for e in entries if getattr(e, "transaction_type", getattr(e, "type", "")).lower() in ("expense", "expenses"))
        saving = sum(e.amount for e in entries if getattr(e, "transaction_type", getattr(e, "type", "")).lower() in ("saving", "savings"))
        return {
            "income": income,
            "expense": expense,
            "saving": saving,
            "net_flow": income - expense - saving
        }
