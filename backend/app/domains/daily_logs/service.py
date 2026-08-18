"""
Domain Application Services for Daily Logs and Spontaneous Notes.
Contains domain business logic decoupled from HTTP frameworks.
"""

from typing import List, Optional
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.daily_logs.interfaces import IDailyLogRepository, ISpontaneousNoteRepository

class DailyLogsService:
    def __init__(self, repo: IDailyLogRepository):
        self.repo = repo

    def get_log(self, log_date: date) -> models.DailyLog:
        db_log = self.repo.get_by_date(log_date)
        if not db_log:
            raise EntityNotFoundException(entity_name="DailyLog", identifier=str(log_date))
        return db_log

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyLog]:
        return self.repo.list_logs(start_date=start_date, end_date=end_date)

    def save_log(self, log_in: schemas.DailyLogCreate) -> models.DailyLog:
        return self.repo.upsert(log_in)

    def delete_log(self, log_date: date) -> bool:
        success = self.repo.delete(log_date)
        if not success:
            raise EntityNotFoundException(entity_name="DailyLog", identifier=str(log_date))
        return True

class NotesService:
    def __init__(self, repo: ISpontaneousNoteRepository):
        self.repo = repo

    def create_note(self, note_in: schemas.SpontaneousNoteCreate) -> models.SpontaneousNote:
        return self.repo.create(note_in)

    def get_undisplayed_notes(self) -> List[models.SpontaneousNote]:
        return self.repo.get_undisplayed()

    def get_notes_by_date(self, target_date: date) -> List[models.SpontaneousNote]:
        return self.repo.get_by_date(target_date)

    def mark_displayed(self, note_ids: List[int]) -> bool:
        return self.repo.mark_displayed(note_ids)
