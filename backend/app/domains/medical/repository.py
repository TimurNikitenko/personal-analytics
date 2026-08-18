"""
SQLAlchemy repository implementations for Medical Tests and Global Metrics.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.medical.interfaces import IMedicalTestRepository, IMetricRepository

class SQLAlchemyMedicalTestRepository(IMedicalTestRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_tests(self, start_date: Optional[date] = None, end_date: Optional[date] = None, test_name: Optional[str] = None) -> List[models.MedicalTest]:
        query = self.db.query(models.MedicalTest)
        if start_date:
            query = query.filter(models.MedicalTest.date >= start_date)
        if end_date:
            query = query.filter(models.MedicalTest.date <= end_date)
        if test_name:
            query = query.filter(models.MedicalTest.test_name.ilike(f"%{test_name}%"))
        return query.order_by(models.MedicalTest.date.desc()).all()

    def upsert_test(self, test_in: schemas.MedicalTestCreate) -> models.MedicalTest:
        db_test = self.db.query(models.MedicalTest).filter(
            models.MedicalTest.date == test_in.date,
            models.MedicalTest.test_name == test_in.test_name
        ).first()

        if db_test:
            for key, value in test_in.model_dump(exclude_unset=True).items():
                setattr(db_test, key, value)
        else:
            db_test = models.MedicalTest(**test_in.model_dump())
            self.db.add(db_test)

        self.db.commit()
        self.db.refresh(db_test)
        return db_test

    def delete_test(self, test_id: int) -> bool:
        db_test = self.db.query(models.MedicalTest).filter(models.MedicalTest.id == test_id).first()
        if db_test:
            self.db.delete(db_test)
            self.db.commit()
            return True
        return False

class SQLAlchemyMetricRepository(IMetricRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_metrics(self, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.GlobalMetric]:
        query = self.db.query(models.GlobalMetric)
        if metric_name:
            query = query.filter(models.GlobalMetric.metric_name == metric_name)
        if start_date:
            query = query.filter(models.GlobalMetric.date >= start_date)
        if end_date:
            query = query.filter(models.GlobalMetric.date <= end_date)
        return query.order_by(models.GlobalMetric.date.desc()).all()

    def get_metric_names(self) -> List[str]:
        results = self.db.query(models.GlobalMetric.metric_name).distinct().all()
        return [r[0] for r in results]

    def create_metric(self, metric_in: schemas.GlobalMetricCreate) -> models.GlobalMetric:
        db_metric = self.db.query(models.GlobalMetric).filter(
            models.GlobalMetric.date == metric_in.date,
            models.GlobalMetric.metric_name == metric_in.metric_name
        ).first()

        if db_metric:
            db_metric.value = metric_in.value
            db_metric.unit = metric_in.unit
            db_metric.notes = metric_in.notes
        else:
            db_metric = models.GlobalMetric(**metric_in.model_dump())
            self.db.add(db_metric)

        self.db.commit()
        self.db.refresh(db_metric)
        return db_metric
