"""
Domain interfaces and repository protocols for Experiments.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class IExperimentRepository(Protocol):
    def list_experiments(self, status: Optional[str] = None) -> List[models.Experiment]:
        ...

    def get_by_id(self, experiment_id: int) -> Optional[models.Experiment]:
        ...

    def create_experiment(self, experiment_in: schemas.ExperimentCreate) -> models.Experiment:
        ...

    def update_experiment(self, experiment_id: int, experiment_in: schemas.ExperimentUpdate) -> Optional[models.Experiment]:
        ...

    def delete_experiment(self, experiment_id: int) -> bool:
        ...

    def list_days(self, experiment_id: int) -> List[models.ExperimentDay]:
        ...

    def upsert_day(self, experiment_id: int, day_in: schemas.ExperimentDayCreate) -> models.ExperimentDay:
        ...

    def delete_day(self, experiment_id: int, date_val: date) -> bool:
        ...
