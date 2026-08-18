import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.experiments.repository import SQLAlchemyExperimentRepository
from backend.app.domains.experiments.service import ExperimentsService

router = APIRouter(prefix="/experiments", tags=["Experiments"])

def get_experiments_service(db: Session = Depends(get_db)) -> ExperimentsService:
    repo = SQLAlchemyExperimentRepository(db)
    return ExperimentsService(repo, db=db)

@router.get("/", response_model=List[schemas.Experiment])
@router.get("", response_model=List[schemas.Experiment])
def read_experiments(
    status_filter: Optional[str] = None,
    service: ExperimentsService = Depends(get_experiments_service)
):
    return service.list_experiments(status=status_filter)

@router.get("/helpers/baseline-stats")
def get_metric_baseline_stats(
    metric_source: str,
    metric_name: str,
    service: ExperimentsService = Depends(get_experiments_service)
):
    return service.get_baseline_stats(metric_source=metric_source, metric_name=metric_name)

@router.get("/{experiment_id}", response_model=schemas.Experiment)
def read_experiment(experiment_id: int, service: ExperimentsService = Depends(get_experiments_service)):
    try:
        return service.get_experiment(experiment_id)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=schemas.Experiment)
@router.post("", response_model=schemas.Experiment)
def create_experiment(
    experiment_in: schemas.ExperimentCreate,
    service: ExperimentsService = Depends(get_experiments_service)
):
    return service.create_experiment(experiment_in)

@router.put("/{experiment_id}", response_model=schemas.Experiment)
def update_experiment(
    experiment_id: int,
    experiment_in: schemas.ExperimentUpdate,
    service: ExperimentsService = Depends(get_experiments_service)
):
    try:
        return service.update_experiment(experiment_id, experiment_in)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, service: ExperimentsService = Depends(get_experiments_service)):
    try:
        service.delete_experiment(experiment_id)
        return {"status": "success", "detail": "Experiment deleted"}
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{experiment_id}/days", response_model=List[schemas.ExperimentDay])
def read_experiment_days(experiment_id: int, service: ExperimentsService = Depends(get_experiments_service)):
    return service.list_days(experiment_id)

@router.post("/{experiment_id}/days", response_model=schemas.ExperimentDay)
def log_experiment_day(
    experiment_id: int,
    day_in: schemas.ExperimentDayCreate,
    service: ExperimentsService = Depends(get_experiments_service)
):
    try:
        return service.upsert_day(experiment_id, day_in)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{experiment_id}/days/{date_str}")
def delete_experiment_day(
    experiment_id: int,
    date_str: str,
    service: ExperimentsService = Depends(get_experiments_service)
):
    try:
        date_val = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        service.delete_day(experiment_id, date_val)
        return {"status": "success", "detail": "Experiment day deleted"}
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{experiment_id}/analyze")
def analyze_experiment(experiment_id: int, service: ExperimentsService = Depends(get_experiments_service)):
    try:
        return service.analyze(experiment_id)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
