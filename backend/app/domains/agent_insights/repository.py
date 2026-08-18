"""
SQLAlchemy repository implementation for Agent Insights.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.agent_insights.interfaces import IAgentInsightRepository

class SQLAlchemyAgentInsightRepository(IAgentInsightRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_insights(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.AgentInsight]:
        query = self.db.query(models.AgentInsight)
        if start_date:
            query = query.filter(models.AgentInsight.date >= start_date)
        if end_date:
            query = query.filter(models.AgentInsight.date <= end_date)
        return query.order_by(models.AgentInsight.created_at.desc()).all()

    def create_insight(self, insight_in: schemas.AgentInsightCreate) -> models.AgentInsight:
        db_insight = models.AgentInsight(**insight_in.model_dump())
        self.db.add(db_insight)
        self.db.commit()
        self.db.refresh(db_insight)
        return db_insight

    def delete_insight(self, insight_id: int) -> bool:
        db_insight = self.db.query(models.AgentInsight).filter(models.AgentInsight.id == insight_id).first()
        if db_insight:
            self.db.delete(db_insight)
            self.db.commit()
            return True
        return False
