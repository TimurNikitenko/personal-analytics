from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/finances", tags=["Finances"])

@router.get("/", response_model=List[schemas.Finance])
@router.get("", response_model=List[schemas.Finance])
def read_finances(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return crud.get_finances(db, start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.Finance)
@router.post("", response_model=schemas.Finance)
def create_finance(finance_in: schemas.FinanceCreate, db: Session = Depends(get_db)):
    return crud.create_finance_entry(db, finance_in=finance_in)

@router.post("/bulk", response_model=List[schemas.Finance])
def create_bulk_finances(finance_ins: List[schemas.FinanceCreate], db: Session = Depends(get_db)):
    return crud.bulk_create_finance_entries(db, finance_ins=finance_ins)

@router.delete("/{finance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finance(finance_id: int, db: Session = Depends(get_db)):
    success = crud.delete_finance_entry(db, finance_id=finance_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finance entry with ID {finance_id} not found"
        )
    return
