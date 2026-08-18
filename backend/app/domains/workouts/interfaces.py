"""
Domain interfaces and repository protocols for Strength Workouts.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IWorkoutRepository(Protocol):
    def list_workouts(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.StrengthWorkout]:
        ...

    def get_by_id(self, workout_id: int) -> Optional[models.StrengthWorkout]:
        ...

    def create_workout(self, workout_in: schemas.StrengthWorkoutCreate) -> models.StrengthWorkout:
        ...

    def delete_workout(self, workout_id: int) -> bool:
        ...
