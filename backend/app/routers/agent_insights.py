from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.agent_insights.repository import SQLAlchemyAgentInsightRepository
from backend.app.domains.agent_insights.service import AgentInsightsService

router = APIRouter(prefix="/agent-insights", tags=["Agent Insights"])

def get_agent_insights_service(db: Session = Depends(get_db)) -> AgentInsightsService:
    repo = SQLAlchemyAgentInsightRepository(db)
    return AgentInsightsService(repo)

@router.get("/", response_model=List[schemas.AgentInsight])
@router.get("", response_model=List[schemas.AgentInsight])
def read_agent_insights(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: AgentInsightsService = Depends(get_agent_insights_service)
):
    return service.list_insights(start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.AgentInsight)
@router.post("", response_model=schemas.AgentInsight)
def create_agent_insight(
    insight_in: schemas.AgentInsightCreate,
    service: AgentInsightsService = Depends(get_agent_insights_service)
):
    return service.create_insight(insight_in)

@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_insight(
    insight_id: int,
    service: AgentInsightsService = Depends(get_agent_insights_service)
):
    try:
        service.delete_insight(insight_id)
        return
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
