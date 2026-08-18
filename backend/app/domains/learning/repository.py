"""
SQLAlchemy repository implementation for Learning Logs.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.learning.interfaces import ILearningRepository

class SQLAlchemyLearningRepository(ILearningRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.LearningLog]:
        query = self.db.query(models.LearningLog)
        if start_date:
            query = query.filter(models.LearningLog.date >= start_date)
        if end_date:
            query = query.filter(models.LearningLog.date <= end_date)
        return query.order_by(models.LearningLog.date.desc()).all()

    def create_entry(self, learning_in: schemas.LearningLogCreate) -> models.LearningLog:
        db_learning = models.LearningLog(**learning_in.model_dump())
        self.db.add(db_learning)
        self.db.commit()
        self.db.refresh(db_learning)
        return db_learning

    def delete_entry(self, learning_id: int) -> bool:
        db_learning = self.db.query(models.LearningLog).filter(models.LearningLog.id == learning_id).first()
        if db_learning:
            self.db.delete(db_learning)
            self.db.commit()
            return True
        return False
