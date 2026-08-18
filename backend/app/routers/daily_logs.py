from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.daily_logs.repository import SQLAlchemyDailyLogRepository
from backend.app.domains.daily_logs.service import DailyLogsService

router = APIRouter(prefix="/daily-logs", tags=["Daily Logs"])

def get_daily_logs_service(db: Session = Depends(get_db)) -> DailyLogsService:
    repo = SQLAlchemyDailyLogRepository(db)
    return DailyLogsService(repo)

@router.get("/", response_model=List[schemas.DailyLog])
@router.get("", response_model=List[schemas.DailyLog])
def read_daily_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: DailyLogsService = Depends(get_daily_logs_service)
):
    return service.list_logs(start_date=start_date, end_date=end_date)

@router.get("/{log_date}", response_model=schemas.DailyLog)
def read_daily_log(log_date: date, service: DailyLogsService = Depends(get_daily_logs_service)):
    try:
        return service.get_log(log_date)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=schemas.DailyLog)
@router.post("", response_model=schemas.DailyLog)
def create_or_update_daily_log(
    log_in: schemas.DailyLogCreate,
    service: DailyLogsService = Depends(get_daily_logs_service)
):
    return service.save_log(log_in)

@router.delete("/{log_date}")
def delete_daily_log(log_date: date, service: DailyLogsService = Depends(get_daily_logs_service)):
    try:
        service.delete_log(log_date)
        return {"detail": f"Daily log for {log_date} deleted successfully"}
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
