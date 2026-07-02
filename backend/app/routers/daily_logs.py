from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/daily-logs", tags=["Daily Logs"])

@router.get("/", response_model=List[schemas.DailyLog])
@router.get("", response_model=List[schemas.DailyLog])
def read_daily_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return crud.get_daily_logs(db, start_date=start_date, end_date=end_date)

@router.get("/{log_date}", response_model=schemas.DailyLog)
def read_daily_log(log_date: date, db: Session = Depends(get_db)):
    db_log = crud.get_daily_log(db, log_date=log_date)
    if not db_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log for {log_date} not found"
        )
    return db_log

@router.post("/", response_model=schemas.DailyLog)
@router.post("", response_model=schemas.DailyLog)
def create_or_update_daily_log(
    log_in: schemas.DailyLogCreate,
    db: Session = Depends(get_db)
):
    return crud.upsert_daily_log(db, log_in=log_in)

@router.delete("/{log_date}")
def delete_daily_log(log_date: date, db: Session = Depends(get_db)):
    success = crud.delete_daily_log(db, log_date=log_date)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log for {log_date} not found"
        )
    return {"detail": f"Daily log for {log_date} deleted successfully"}
