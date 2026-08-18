from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.nutrition.repository import SQLAlchemyNutritionRepository
from backend.app.domains.nutrition.service import NutritionService

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])

def get_nutrition_service(db: Session = Depends(get_db)) -> NutritionService:
    repo = SQLAlchemyNutritionRepository(db)
    return NutritionService(repo)

@router.get("/", response_model=List[schemas.DailyNutrition])
@router.get("", response_model=List[schemas.DailyNutrition])
def read_nutrition_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: NutritionService = Depends(get_nutrition_service)
):
    return service.list_logs(start_date=start_date, end_date=end_date)

@router.get("/{log_date}", response_model=schemas.DailyNutrition)
def read_nutrition_log(log_date: date, service: NutritionService = Depends(get_nutrition_service)):
    try:
        return service.get_log(log_date)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=schemas.DailyNutrition)
@router.post("", response_model=schemas.DailyNutrition)
def write_nutrition_log(
    nutrition_in: schemas.DailyNutritionCreate,
    service: NutritionService = Depends(get_nutrition_service)
):
    return service.save_log(nutrition_in)

@router.delete("/{log_date}")
def remove_nutrition_log(log_date: date, service: NutritionService = Depends(get_nutrition_service)):
    try:
        service.delete_log(log_date)
        return {"detail": "Nutrition log deleted successfully"}
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
