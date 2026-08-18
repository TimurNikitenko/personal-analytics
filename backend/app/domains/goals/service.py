"""
Domain Application Service for Goals Tracking.
"""

from typing import List, Optional
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.goals.interfaces import IGoalRepository

class GoalsService:
    def __init__(self, repo: IGoalRepository):
        self.repo = repo

    def list_goals(self, status: Optional[str] = None) -> List[models.Goal]:
        return self.repo.list_goals(status=status)

    def create_goal(self, goal_in: schemas.GoalCreate) -> models.Goal:
        return self.repo.create_goal(goal_in)

    def update_goal(self, goal_id: int, goal_in: schemas.GoalCreate) -> models.Goal:
        db_goal = self.repo.update_goal(goal_id, goal_in)
        if not db_goal:
            raise EntityNotFoundException(entity_name="Goal", identifier=str(goal_id))
        return db_goal

    def delete_goal(self, goal_id: int) -> bool:
        success = self.repo.delete_goal(goal_id)
        if not success:
            raise EntityNotFoundException(entity_name="Goal", identifier=str(goal_id))
        return True
