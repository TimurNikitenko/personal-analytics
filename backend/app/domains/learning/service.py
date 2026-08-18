"""
Domain Application Service for Learning Logs.
"""

from typing import List, Optional
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.learning.interfaces import ILearningRepository

class LearningService:
    def __init__(self, repo: ILearningRepository):
        self.repo = repo

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.LearningLog]:
        return self.repo.list_logs(start_date=start_date, end_date=end_date)

    def create_entry(self, learning_in: schemas.LearningLogCreate) -> models.LearningLog:
        return self.repo.create_entry(learning_in)

    def delete_entry(self, learning_id: int) -> bool:
        success = self.repo.delete_entry(learning_id)
        if not success:
            raise EntityNotFoundException(entity_name="LearningLog", identifier=str(learning_id))
        return True
