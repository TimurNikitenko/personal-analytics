"""
Domain interfaces and repository protocols for Agent Insights.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IAgentInsightRepository(Protocol):
    def list_insights(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.AgentInsight]:
        ...

    def create_insight(self, insight_in: schemas.AgentInsightCreate) -> models.AgentInsight:
        ...

    def delete_insight(self, insight_id: int) -> bool:
        ...
