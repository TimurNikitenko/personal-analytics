"""
SQLAlchemy repository implementation for Experiments.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.experiments.interfaces import IExperimentRepository

class SQLAlchemyExperimentRepository(IExperimentRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_experiments(self, status: Optional[str] = None) -> List[models.Experiment]:
        query = self.db.query(models.Experiment)
        if status:
            query = query.filter(models.Experiment.status == status)
        return query.order_by(models.Experiment.created_at.desc()).all()

    def get_by_id(self, experiment_id: int) -> Optional[models.Experiment]:
        return self.db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()

    def create_experiment(self, experiment_in: schemas.ExperimentCreate) -> models.Experiment:
        db_exp = models.Experiment(**experiment_in.model_dump())
        self.db.add(db_exp)
        self.db.commit()
        self.db.refresh(db_exp)
        return db_exp

    def update_experiment(self, experiment_id: int, experiment_in: schemas.ExperimentUpdate) -> Optional[models.Experiment]:
        db_exp = self.get_by_id(experiment_id)
        if db_exp:
            for key, value in experiment_in.model_dump(exclude_unset=True).items():
                setattr(db_exp, key, value)
            self.db.commit()
            self.db.refresh(db_exp)
        return db_exp

    def delete_experiment(self, experiment_id: int) -> bool:
        db_exp = self.get_by_id(experiment_id)
        if db_exp:
            self.db.delete(db_exp)
            self.db.commit()
            return True
        return False

    def list_days(self, experiment_id: int) -> List[models.ExperimentDay]:
        return self.db.query(models.ExperimentDay).filter(models.ExperimentDay.experiment_id == experiment_id).order_by(models.ExperimentDay.date.asc()).all()

    def upsert_day(self, experiment_id: int, day_in: schemas.ExperimentDayCreate) -> models.ExperimentDay:
        db_day = self.db.query(models.ExperimentDay).filter(
            models.ExperimentDay.experiment_id == experiment_id,
            models.ExperimentDay.date == day_in.date
        ).first()

        if db_day:
            db_day.group = day_in.group
            db_day.notes = day_in.notes
        else:
            db_day = models.ExperimentDay(
                experiment_id=experiment_id,
                date=day_in.date,
                group=day_in.group,
                notes=day_in.notes
            )
            self.db.add(db_day)

        self.db.commit()
        self.db.refresh(db_day)
        return db_day

    def delete_day(self, experiment_id: int, date_val: date) -> bool:
        db_day = self.db.query(models.ExperimentDay).filter(
            models.ExperimentDay.experiment_id == experiment_id,
            models.ExperimentDay.date == date_val
        ).first()
        if db_day:
            self.db.delete(db_day)
            self.db.commit()
            return True
        return False
