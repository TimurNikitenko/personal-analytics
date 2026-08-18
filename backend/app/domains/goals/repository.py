"""
SQLAlchemy repository implementation for Goals.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.goals.interfaces import IGoalRepository

class SQLAlchemyGoalRepository(IGoalRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_goals(self, status: Optional[str] = None) -> List[models.Goal]:
        query = self.db.query(models.Goal)
        if status:
            query = query.filter(models.Goal.status == status)
        return query.order_by(models.Goal.start_date.desc()).all()

    def get_by_id(self, goal_id: int) -> Optional[models.Goal]:
        return self.db.query(models.Goal).filter(models.Goal.id == goal_id).first()

    def create_goal(self, goal_in: schemas.GoalCreate) -> models.Goal:
        db_goal = models.Goal(**goal_in.model_dump())
        self.db.add(db_goal)
        self.db.commit()
        self.db.refresh(db_goal)
        return db_goal

    def update_goal(self, goal_id: int, goal_in: schemas.GoalCreate) -> Optional[models.Goal]:
        db_goal = self.get_by_id(goal_id)
        if db_goal:
            for key, value in goal_in.model_dump(exclude_unset=True).items():
                setattr(db_goal, key, value)
            self.db.commit()
            self.db.refresh(db_goal)
        return db_goal

    def delete_goal(self, goal_id: int) -> bool:
        db_goal = self.get_by_id(goal_id)
        if db_goal:
            self.db.delete(db_goal)
            self.db.commit()
            return True
        return False
