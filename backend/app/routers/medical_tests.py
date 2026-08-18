from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.medical.repository import SQLAlchemyMedicalTestRepository
from backend.app.domains.medical.service import MedicalTestsService

router = APIRouter(
    prefix="/medical-tests",
    tags=["Medical Tests"]
)

def get_medical_tests_service(db: Session = Depends(get_db)) -> MedicalTestsService:
    repo = SQLAlchemyMedicalTestRepository(db)
    return MedicalTestsService(repo)

@router.get("/", response_model=List[schemas.MedicalTest])
@router.get("", response_model=List[schemas.MedicalTest])
def read_medical_tests(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    test_name: Optional[str] = None,
    service: MedicalTestsService = Depends(get_medical_tests_service)
):
    return service.list_tests(start_date=start_date, end_date=end_date, test_name=test_name)

@router.post("/", response_model=schemas.MedicalTest)
@router.post("", response_model=schemas.MedicalTest)
def write_medical_test(
    test_in: schemas.MedicalTestCreate,
    service: MedicalTestsService = Depends(get_medical_tests_service)
):
    return service.save_test(test_in)

@router.delete("/{test_id}")
def remove_medical_test(
    test_id: int,
    service: MedicalTestsService = Depends(get_medical_tests_service)
):
    try:
        service.delete_test(test_id)
        return {"detail": "Medical test entry deleted successfully"}
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
