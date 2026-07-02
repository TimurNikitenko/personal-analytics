from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.get("/", response_model=List[schemas.Goal])
@router.get("", response_model=List[schemas.Goal])
def read_goals(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_goals(db, status=status)

@router.post("/", response_model=schemas.Goal)
@router.post("", response_model=schemas.Goal)
def create_goal(goal_in: schemas.GoalCreate, db: Session = Depends(get_db)):
    return crud.create_goal(db, goal_in=goal_in)

@router.put("/{goal_id}", response_model=schemas.Goal)
def update_goal(goal_id: int, goal_in: schemas.GoalCreate, db: Session = Depends(get_db)):
    db_goal = crud.update_goal(db, goal_id=goal_id, goal_in=goal_in)
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with ID {goal_id} not found"
        )
    return db_goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    success = crud.delete_goal(db, goal_id=goal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with ID {goal_id} not found"
        )
    return
