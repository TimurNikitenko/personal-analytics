"""
Domain interfaces and repository protocols for Medical Tests and Global Metrics.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IMedicalTestRepository(Protocol):
    def list_tests(self, start_date: Optional[date] = None, end_date: Optional[date] = None, test_name: Optional[str] = None) -> List[models.MedicalTest]:
        ...

    def upsert_test(self, test_in: schemas.MedicalTestCreate) -> models.MedicalTest:
        ...

    def delete_test(self, test_id: int) -> bool:
        ...

class IMetricRepository(Protocol):
    def list_metrics(self, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.GlobalMetric]:
        ...

    def get_metric_names(self) -> List[str]:
        ...

    def create_metric(self, metric_in: schemas.GlobalMetricCreate) -> models.GlobalMetric:
        ...
