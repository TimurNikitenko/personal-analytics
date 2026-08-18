from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.learning.repository import SQLAlchemyLearningRepository
from backend.app.domains.learning.service import LearningService

router = APIRouter(prefix="/learning", tags=["Learning"])

def get_learning_service(db: Session = Depends(get_db)) -> LearningService:
    repo = SQLAlchemyLearningRepository(db)
    return LearningService(repo)

@router.get("/", response_model=List[schemas.LearningLog])
@router.get("", response_model=List[schemas.LearningLog])
def read_learning_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: LearningService = Depends(get_learning_service)
):
    return service.list_logs(start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.LearningLog)
@router.post("", response_model=schemas.LearningLog)
def create_learning(
    learning_in: schemas.LearningLogCreate,
    service: LearningService = Depends(get_learning_service)
):
    return service.create_entry(learning_in)

@router.delete("/{learning_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning(
    learning_id: int,
    service: LearningService = Depends(get_learning_service)
):
    try:
        service.delete_entry(learning_id)
        return
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
