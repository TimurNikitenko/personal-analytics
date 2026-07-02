from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import crud, schemas, database

router = APIRouter(
    prefix="/medical-tests",
    tags=["Medical Tests"]
)

@router.get("/", response_model=List[schemas.MedicalTest])
@router.get("", response_model=List[schemas.MedicalTest])
def read_medical_tests(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    test_name: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    return crud.get_medical_tests(db, start_date=start_date, end_date=end_date, test_name=test_name)

@router.post("/", response_model=schemas.MedicalTest)
@router.post("", response_model=schemas.MedicalTest)
def write_medical_test(
    test_in: schemas.MedicalTestCreate,
    db: Session = Depends(database.get_db)
):
    return crud.upsert_medical_test(db, test_in=test_in)

@router.delete("/{test_id}")
def remove_medical_test(test_id: int, db: Session = Depends(database.get_db)):
    success = crud.delete_medical_test(db, test_id=test_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medical test entry with ID {test_id} not found"
        )
    return {"detail": "Medical test entry deleted successfully"}
