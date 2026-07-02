from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/learning", tags=["Learning"])

@router.get("/", response_model=List[schemas.LearningLog])
@router.get("", response_model=List[schemas.LearningLog])
def read_learning_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return crud.get_learning_logs(db, start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.LearningLog)
@router.post("", response_model=schemas.LearningLog)
def create_learning(learning_in: schemas.LearningLogCreate, db: Session = Depends(get_db)):
    return crud.create_learning_entry(db, learning_in=learning_in)

@router.delete("/{learning_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning(learning_id: int, db: Session = Depends(get_db)):
    success = crud.delete_learning_entry(db, learning_id=learning_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning log with ID {learning_id} not found"
        )
    return
