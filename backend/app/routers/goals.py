from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.goals.repository import SQLAlchemyGoalRepository
from backend.app.domains.goals.service import GoalsService

router = APIRouter(prefix="/goals", tags=["Goals"])

def get_goals_service(db: Session = Depends(get_db)) -> GoalsService:
    repo = SQLAlchemyGoalRepository(db)
    return GoalsService(repo)

@router.get("/", response_model=List[schemas.Goal])
@router.get("", response_model=List[schemas.Goal])
def read_goals(
    status_filter: Optional[str] = None,
    service: GoalsService = Depends(get_goals_service)
):
    return service.list_goals(status=status_filter)

@router.post("/", response_model=schemas.Goal)
@router.post("", response_model=schemas.Goal)
def create_goal(
    goal_in: schemas.GoalCreate,
    service: GoalsService = Depends(get_goals_service)
):
    return service.create_goal(goal_in)

@router.put("/{goal_id}", response_model=schemas.Goal)
def update_goal(
    goal_id: int,
    goal_in: schemas.GoalCreate,
    service: GoalsService = Depends(get_goals_service)
):
    try:
        return service.update_goal(goal_id, goal_in)
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    service: GoalsService = Depends(get_goals_service)
):
    try:
        service.delete_goal(goal_id)
        return
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
