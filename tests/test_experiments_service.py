from datetime import date
import pytest
from backend.app.schemas import ExperimentCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.experiments.service import ExperimentsService

class MockExperimentRepo:
    def __init__(self):
        self.exps = {}
        self.days = []

    def list_experiments(self, status=None):
        return list(self.exps.values())

    def get_by_id(self, experiment_id: int):
        return self.exps.get(experiment_id)

    def create_experiment(self, experiment_in: ExperimentCreate):
        class DummyExp:
            def __init__(self, eid, title, status, etype, mname, msrc, start):
                self.id = eid
                self.title = title
                self.status = status
                self.experiment_type = etype
                self.metric_name = mname
                self.metric_source = msrc
                self.start_date = start
                self.end_date = None
                self.alpha = 0.05
                self.mde = 0.1
                self.results_summary = None

        eid = len(self.exps) + 1
        obj = DummyExp(eid, experiment_in.title, experiment_in.status, experiment_in.experiment_type, experiment_in.metric_name, experiment_in.metric_source, experiment_in.start_date)
        self.exps[eid] = obj
        return obj

    def update_experiment(self, experiment_id, experiment_in):
        if experiment_id in self.exps:
            self.exps[experiment_id].title = experiment_in.title or self.exps[experiment_id].title
            return self.exps[experiment_id]
        return None

    def delete_experiment(self, experiment_id: int):
        if experiment_id in self.exps:
            del self.exps[experiment_id]
            return True
        return False

    def list_days(self, experiment_id: int):
        return [d for d in self.days if d.experiment_id == experiment_id]

    def upsert_day(self, experiment_id, day_in):
        class DummyDay:
            def __init__(self, eid, d, group):
                self.experiment_id = eid
                self.date = d
                self.group = group
                self.notes = None
        obj = DummyDay(experiment_id, day_in.date, day_in.group)
        self.days.append(obj)
        return obj

    def delete_day(self, experiment_id, date_val):
        self.days = [d for d in self.days if not (d.experiment_id == experiment_id and d.date == date_val)]
        return True

def test_experiments_service_crud():
    repo = MockExperimentRepo()
    service = ExperimentsService(repo)

    e_in = ExperimentCreate(
        title="Matcha Tea Experiment",
        hypothesis="Matcha improves HRV",
        intervention_description="Drink 1 cup of Matcha every morning",
        experiment_type="pre_post",
        metric_source="global_metrics",
        metric_name="HRV",
        start_date=date(2026, 8, 1),
        status="Active"
    )
    created = service.create_experiment(e_in)
    assert created.title == "Matcha Tea Experiment"
    assert created.id == 1

    retrieved = service.get_experiment(1)
    assert retrieved.title == "Matcha Tea Experiment"

    assert service.delete_experiment(1) is True
    with pytest.raises(EntityNotFoundException):
        service.get_experiment(1)
