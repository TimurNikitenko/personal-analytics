"""
SQLAlchemy repository implementations for Daily Logs and Spontaneous Notes.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.daily_logs.interfaces import IDailyLogRepository, ISpontaneousNoteRepository

class SQLAlchemyDailyLogRepository(IDailyLogRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_date(self, log_date: date) -> Optional[models.DailyLog]:
        return self.db.query(models.DailyLog).filter(models.DailyLog.date == log_date).first()

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyLog]:
        query = self.db.query(models.DailyLog)
        if start_date:
            query = query.filter(models.DailyLog.date >= start_date)
        if end_date:
            query = query.filter(models.DailyLog.date <= end_date)
        return query.order_by(models.DailyLog.date.desc()).all()

    def upsert(self, log_in: schemas.DailyLogCreate) -> models.DailyLog:
        db_log = self.get_by_date(log_in.date)
        
        if db_log:
            log_data = log_in.model_dump(exclude={"supplements"}, exclude_unset=True)
            for key, value in log_data.items():
                setattr(db_log, key, value)
        else:
            log_data = log_in.model_dump(exclude={"supplements"})
            db_log = models.DailyLog(**log_data)
            self.db.add(db_log)
        
        self.db.commit()
        self.db.refresh(db_log)
        
        if "supplements" in log_in.model_fields_set:
            self.db.query(models.DailySupplement).filter(models.DailySupplement.date == log_in.date).delete()
            for supp_in in log_in.supplements:
                db_supp = models.DailySupplement(
                    date=log_in.date,
                    name=supp_in.name,
                    dosage=supp_in.dosage,
                    unit=supp_in.unit
                )
                self.db.add(db_supp)
            self.db.commit()
            self.db.refresh(db_log)

        return db_log

    def delete(self, log_date: date) -> bool:
        db_log = self.get_by_date(log_date)
        if db_log:
            self.db.delete(db_log)
            self.db.commit()
            return True
        return False

class SQLAlchemySpontaneousNoteRepository(ISpontaneousNoteRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, note_in: schemas.SpontaneousNoteCreate) -> models.SpontaneousNote:
        db_note = models.SpontaneousNote(**note_in.model_dump())
        self.db.add(db_note)
        self.db.commit()
        self.db.refresh(db_note)
        return db_note

    def get_undisplayed(self) -> List[models.SpontaneousNote]:
        return self.db.query(models.SpontaneousNote).filter(models.SpontaneousNote.displayed == False).order_by(models.SpontaneousNote.created_at.desc()).all()

    def get_by_date(self, target_date: date) -> List[models.SpontaneousNote]:
        return self.db.query(models.SpontaneousNote).filter(models.SpontaneousNote.date == target_date).order_by(models.SpontaneousNote.created_at.desc()).all()

    def mark_displayed(self, note_ids: List[int]) -> bool:
        self.db.query(models.SpontaneousNote).filter(models.SpontaneousNote.id.in_(note_ids)).update({"displayed": True}, synchronize_session=False)
        self.db.commit()
        return True
