"""
SQLAlchemy repository implementation for Finances.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.finances.interfaces import IFinanceRepository

class SQLAlchemyFinanceRepository(IFinanceRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_entries(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Finance]:
        query = self.db.query(models.Finance)
        if start_date:
            query = query.filter(models.Finance.date >= start_date)
        if end_date:
            query = query.filter(models.Finance.date <= end_date)
        return query.order_by(models.Finance.date.desc()).all()

    def create_entry(self, finance_in: schemas.FinanceCreate) -> models.Finance:
        db_finance = models.Finance(**finance_in.model_dump())
        self.db.add(db_finance)
        self.db.commit()
        self.db.refresh(db_finance)
        return db_finance

    def bulk_create_entries(self, finance_ins: List[schemas.FinanceCreate]) -> List[models.Finance]:
        db_entries = [models.Finance(**entry.model_dump()) for entry in finance_ins]
        self.db.add_all(db_entries)
        self.db.commit()
        for entry in db_entries:
            self.db.refresh(entry)
        return db_entries

    def delete_entry(self, finance_id: int) -> bool:
        db_finance = self.db.query(models.Finance).filter(models.Finance.id == finance_id).first()
        if db_finance:
            self.db.delete(db_finance)
            self.db.commit()
            return True
        return False
