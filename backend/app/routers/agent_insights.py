from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/agent-insights", tags=["Agent Insights"])

@router.get("/", response_model=List[schemas.AgentInsight])
@router.get("", response_model=List[schemas.AgentInsight])
def read_agent_insights(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return crud.get_agent_insights(db, start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.AgentInsight)
@router.post("", response_model=schemas.AgentInsight)
def create_agent_insight(
    insight_in: schemas.AgentInsightCreate,
    db: Session = Depends(get_db)
):
    return crud.create_agent_insight(db, insight_in=insight_in)

@router.delete("/{insight_id}")
def delete_agent_insight(insight_id: int, db: Session = Depends(get_db)):
    success = crud.delete_agent_insight(db, insight_id=insight_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent insight with ID {insight_id} not found"
        )
    return {"detail": f"Agent insight with ID {insight_id} deleted successfully"}
