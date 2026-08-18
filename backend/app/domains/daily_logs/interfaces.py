"""
Domain interfaces and repository protocols for Daily Logs and Spontaneous Notes.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IDailyLogRepository(Protocol):
    def get_by_date(self, log_date: date) -> Optional[models.DailyLog]:
        ...

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyLog]:
        ...

    def upsert(self, log_in: schemas.DailyLogCreate) -> models.DailyLog:
        ...

    def delete(self, log_date: date) -> bool:
        ...

class ISpontaneousNoteRepository(Protocol):
    def create(self, note_in: schemas.SpontaneousNoteCreate) -> models.SpontaneousNote:
        ...

    def get_undisplayed(self) -> List[models.SpontaneousNote]:
        ...

    def get_by_date(self, target_date: date) -> List[models.SpontaneousNote]:
        ...

    def mark_displayed(self, note_ids: List[int]) -> bool:
        ...
