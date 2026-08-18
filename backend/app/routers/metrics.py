from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.domains.medical.repository import SQLAlchemyMetricRepository
from backend.app.domains.medical.service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    repo = SQLAlchemyMetricRepository(db)
    return MetricsService(repo)

@router.get("/", response_model=List[schemas.GlobalMetric])
@router.get("", response_model=List[schemas.GlobalMetric])
def read_metrics(
    metric_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: MetricsService = Depends(get_metrics_service)
):
    return service.list_metrics(metric_name=metric_name, start_date=start_date, end_date=end_date)

@router.get("/names", response_model=List[str])
def read_metric_names(service: MetricsService = Depends(get_metrics_service)):
    return service.get_metric_names()

@router.post("/", response_model=schemas.GlobalMetric)
@router.post("", response_model=schemas.GlobalMetric)
def create_metric(
    metric_in: schemas.GlobalMetricCreate,
    service: MetricsService = Depends(get_metrics_service)
):
    return service.create_metric(metric_in)
