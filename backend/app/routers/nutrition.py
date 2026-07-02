from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import crud, schemas, database

router = APIRouter(
    prefix="/nutrition",
    tags=["Nutrition"]
)

@router.get("/", response_model=List[schemas.DailyNutrition])
@router.get("", response_model=List[schemas.DailyNutrition])
def read_nutrition_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(database.get_db)
):
    return crud.get_nutrition_logs(db, start_date=start_date, end_date=end_date)

@router.get("/{log_date}", response_model=schemas.DailyNutrition)
def read_nutrition_log(log_date: date, db: Session = Depends(database.get_db)):
    db_nut = crud.get_nutrition_log(db, log_date=log_date)
    if not db_nut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nutrition log for date {log_date} not found"
        )
    return db_nut

@router.post("/", response_model=schemas.DailyNutrition)
@router.post("", response_model=schemas.DailyNutrition)
def write_nutrition_log(
    nutrition_in: schemas.DailyNutritionCreate,
    db: Session = Depends(database.get_db)
):
    return crud.upsert_nutrition_log(db, nutrition_in=nutrition_in)

@router.delete("/{log_date}")
def remove_nutrition_log(log_date: date, db: Session = Depends(database.get_db)):
    success = crud.delete_nutrition_log(db, log_date=log_date)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nutrition log for date {log_date} not found"
        )
    return {"detail": "Nutrition log deleted successfully"}
