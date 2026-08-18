"""
Domain interfaces and repository protocols for Learning Logs.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class ILearningRepository(Protocol):
    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.LearningLog]:
        ...

    def create_entry(self, learning_in: schemas.LearningLogCreate) -> models.LearningLog:
        ...

    def delete_entry(self, learning_id: int) -> bool:
        ...
