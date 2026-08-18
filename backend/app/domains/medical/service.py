"""
Domain Application Services for Medical Tests and Global Metrics.
"""

from typing import List, Optional
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.medical.interfaces import IMedicalTestRepository, IMetricRepository

class MedicalTestsService:
    def __init__(self, repo: IMedicalTestRepository):
        self.repo = repo

    def list_tests(self, start_date: Optional[date] = None, end_date: Optional[date] = None, test_name: Optional[str] = None) -> List[models.MedicalTest]:
        return self.repo.list_tests(start_date=start_date, end_date=end_date, test_name=test_name)

    def save_test(self, test_in: schemas.MedicalTestCreate) -> models.MedicalTest:
        return self.repo.upsert_test(test_in)

    def delete_test(self, test_id: int) -> bool:
        success = self.repo.delete_test(test_id)
        if not success:
            raise EntityNotFoundException(entity_name="MedicalTest", identifier=str(test_id))
        return True

class MetricsService:
    def __init__(self, repo: IMetricRepository):
        self.repo = repo

    def list_metrics(self, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.GlobalMetric]:
        return self.repo.list_metrics(metric_name=metric_name, start_date=start_date, end_date=end_date)

    def get_metric_names(self) -> List[str]:
        return self.repo.get_metric_names()

    def create_metric(self, metric_in: schemas.GlobalMetricCreate) -> models.GlobalMetric:
        return self.repo.create_metric(metric_in)
