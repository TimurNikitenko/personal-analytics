"""
Domain interfaces and repository protocols for Goals.
"""

from typing import Protocol, List, Optional
from backend.app import models, schemas

class IGoalRepository(Protocol):
    def list_goals(self, status: Optional[str] = None) -> List[models.Goal]:
        ...

    def get_by_id(self, goal_id: int) -> Optional[models.Goal]:
        ...

    def create_goal(self, goal_in: schemas.GoalCreate) -> models.Goal:
        ...

    def update_goal(self, goal_id: int, goal_in: schemas.GoalCreate) -> Optional[models.Goal]:
        ...

    def delete_goal(self, goal_id: int) -> bool:
        ...
