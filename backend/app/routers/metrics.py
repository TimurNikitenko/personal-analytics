from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("/", response_model=List[schemas.GlobalMetric])
@router.get("", response_model=List[schemas.GlobalMetric])
def read_metrics(
    metric_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return crud.get_metrics(db, metric_name=metric_name, start_date=start_date, end_date=end_date)

@router.get("/names", response_model=List[str])
def read_metric_names(db: Session = Depends(get_db)):
    return crud.get_metric_names(db)

@router.post("/", response_model=schemas.GlobalMetric)
@router.post("", response_model=schemas.GlobalMetric)
def create_metric(metric_in: schemas.GlobalMetricCreate, db: Session = Depends(get_db)):
    return crud.create_metric_entry(db, metric_in=metric_in)
