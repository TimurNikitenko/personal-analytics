"""
Domain Application Service for Agent Insights.
"""

from typing import List, Optional
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.agent_insights.interfaces import IAgentInsightRepository

class AgentInsightsService:
    def __init__(self, repo: IAgentInsightRepository):
        self.repo = repo

    def list_insights(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.AgentInsight]:
        return self.repo.list_insights(start_date=start_date, end_date=end_date)

    def create_insight(self, insight_in: schemas.AgentInsightCreate) -> models.AgentInsight:
        return self.repo.create_insight(insight_in)

    def delete_insight(self, insight_id: int) -> bool:
        success = self.repo.delete_insight(insight_id)
        if not success:
            raise EntityNotFoundException(entity_name="AgentInsight", identifier=str(insight_id))
        return True
