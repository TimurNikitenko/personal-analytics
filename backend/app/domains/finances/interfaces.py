"""
Domain interfaces and repository protocols for Finances.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IFinanceRepository(Protocol):
    def list_entries(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Finance]:
        ...

    def create_entry(self, finance_in: schemas.FinanceCreate) -> models.Finance:
        ...

    def bulk_create_entries(self, finance_ins: List[schemas.FinanceCreate]) -> List[models.Finance]:
        ...

    def delete_entry(self, finance_id: int) -> bool:
        ...
