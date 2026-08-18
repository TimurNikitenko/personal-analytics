from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException, ValidationErrorException
from backend.app.domains.workouts.repository import SQLAlchemyWorkoutRepository
from backend.app.domains.workouts.service import WorkoutsService

router = APIRouter(
    prefix="/strength-workouts",
    tags=["Strength Workouts"]
)

def get_workouts_service(db: Session = Depends(get_db)) -> WorkoutsService:
    repo = SQLAlchemyWorkoutRepository(db)
    return WorkoutsService(repo, db=db)

@router.get("/", response_model=List[schemas.StrengthWorkout])
def read_strength_workouts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: WorkoutsService = Depends(get_workouts_service)
):
    return service.list_workouts(start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.StrengthWorkout)
def create_strength_workout(
    workout: schemas.StrengthWorkoutCreate,
    service: WorkoutsService = Depends(get_workouts_service)
):
    return service.create_workout(workout)

@router.delete("/{workout_id}")
def delete_strength_workout(
    workout_id: int,
    service: WorkoutsService = Depends(get_workouts_service)
):
    try:
        service.delete_workout(workout_id)
        return {"status": "success", "message": f"Workout {workout_id} deleted"}
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/import")
def import_workouts_csv(
    file: UploadFile = File(...),
    service: WorkoutsService = Depends(get_workouts_service)
):
    try:
        content = file.file.read()
        return service.import_csv(content)
    except ValidationErrorException as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process CSV file: {str(e)}")
