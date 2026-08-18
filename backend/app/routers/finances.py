from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.finances.repository import SQLAlchemyFinanceRepository
from backend.app.domains.finances.service import FinancesService

router = APIRouter(prefix="/finances", tags=["Finances"])

def get_finances_service(db: Session = Depends(get_db)) -> FinancesService:
    repo = SQLAlchemyFinanceRepository(db)
    return FinancesService(repo)

@router.get("/", response_model=List[schemas.Finance])
@router.get("", response_model=List[schemas.Finance])
def read_finances(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: FinancesService = Depends(get_finances_service)
):
    return service.list_entries(start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.Finance)
@router.post("", response_model=schemas.Finance)
def create_finance(
    finance_in: schemas.FinanceCreate,
    service: FinancesService = Depends(get_finances_service)
):
    return service.create_entry(finance_in)

@router.post("/bulk", response_model=List[schemas.Finance])
def create_bulk_finances(
    finance_ins: List[schemas.FinanceCreate],
    service: FinancesService = Depends(get_finances_service)
):
    return service.bulk_create_entries(finance_ins)

@router.delete("/{finance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finance(
    finance_id: int,
    service: FinancesService = Depends(get_finances_service)
):
    try:
        service.delete_entry(finance_id)
        return
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
