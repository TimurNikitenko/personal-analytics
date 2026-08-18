from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional, List, Dict, Any
from backend.app.database import engine
from backend.app.domains.ml.service import MLDatasetService

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

def get_ml_service() -> MLDatasetService:
    return MLDatasetService(engine=engine)

@router.get("/dataset")
def get_ml_dataset(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: MLDatasetService = Depends(get_ml_service)
) -> List[Dict[str, Any]]:
    """
    Generates a flattened, unified tabular dataset of all numerical and pivoted metrics
    grouped by date. Perfect for importing into Pandas or training ML models.
    """
    return service.build_flattened_dataset(start_date=start_date, end_date=end_date)
