"""
Domain Application Service for Experiments & Statistical Engine.
Encapsulates Statistical Power Analysis, Shapiro-Wilk testing, Mann-Whitney/T-test selection,
Bootstrap modeling, and Experiment Day management.
"""

import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app import models, schemas, crud
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.experiments.interfaces import IExperimentRepository
from backend.app.utils.statistics import (
    analyze_experiment_data,
    calculate_required_sample_size,
    estimate_baseline_stats
)

class ExperimentsService:
    def __init__(self, repo: IExperimentRepository, db: Optional[Session] = None):
        self.repo = repo
        self.db = db

    def list_experiments(self, status: Optional[str] = None) -> List[models.Experiment]:
        return self.repo.list_experiments(status=status)

    def get_experiment(self, experiment_id: int) -> models.Experiment:
        exp = self.repo.get_by_id(experiment_id)
        if not exp:
            raise EntityNotFoundException(entity_name="Experiment", identifier=str(experiment_id))
        return exp

    def _get_metric_values_by_date(self, metric_source: str, metric_name: str) -> Dict[datetime.date, float]:
        if not self.db:
            return {}
        res = {}
        if metric_source == "daily_logs":
            logs = crud.get_daily_logs(self.db)
            for log in logs:
                val = None
                if metric_name == "sleep_hours":
                    if log.sleep_start and log.sleep_end:
                        diff = log.sleep_end - log.sleep_start
                        val = diff.total_seconds() / 3600.0
                else:
                    val = getattr(log, metric_name, None)
                if val is not None:
                    res[log.date] = float(val)
        elif metric_source == "global_metrics":
            metrics = crud.get_metrics(self.db, metric_name=metric_name)
            for m in metrics:
                try:
                    res[m.date] = float(m.metric_value)
                except (ValueError, TypeError, AttributeError):
                    pass
        elif metric_source == "learning_logs":
            logs = crud.get_learning_logs(self.db)
            for log in logs:
                val = log.learning_hours + log.practice_hours if metric_name == "total_hours" else getattr(log, metric_name, None)
                if val is not None:
                    res[log.date] = float(val)
        elif metric_source == "daily_nutrition":
            logs = crud.get_nutrition_logs(self.db)
            for log in logs:
                val = getattr(log, metric_name, None)
                if val is not None:
                    res[log.date] = float(val)
        elif metric_source == "medical_tests":
            tests = crud.get_medical_tests(self.db, test_name=metric_name)
            for t in tests:
                res[t.date] = float(t.value)
        return res

    def get_baseline_stats(self, metric_source: str, metric_name: str) -> Dict[str, Any]:
        metric_values = list(self._get_metric_values_by_date(metric_source, metric_name).values())
        if not metric_values:
            return {"n": 0, "mean": 0.0, "std": 0.0}
        mean, std = estimate_baseline_stats(metric_values)
        return {"n": len(metric_values), "mean": mean, "std": std}

    def create_experiment(self, experiment_in: schemas.ExperimentCreate) -> models.Experiment:
        if experiment_in.mde and experiment_in.mde > 0:
            metric_values = list(self._get_metric_values_by_date(experiment_in.metric_source, experiment_in.metric_name).values())
            mean, std = estimate_baseline_stats(metric_values)
            if std > 0:
                experiment_in.required_sample_size = calculate_required_sample_size(
                    std=std,
                    mde=experiment_in.mde,
                    alpha=experiment_in.alpha,
                    power=experiment_in.power
                )
        return self.repo.create_experiment(experiment_in)

    def update_experiment(self, experiment_id: int, experiment_in: schemas.ExperimentUpdate) -> models.Experiment:
        db_exp = self.get_experiment(experiment_id)
        mde = experiment_in.mde if experiment_in.mde is not None else db_exp.mde
        alpha = experiment_in.alpha if experiment_in.alpha is not None else db_exp.alpha
        power = experiment_in.power if experiment_in.power is not None else db_exp.power
        metric_source = experiment_in.metric_source if experiment_in.metric_source is not None else db_exp.metric_source
        metric_name = experiment_in.metric_name if experiment_in.metric_name is not None else db_exp.metric_name

        if mde and mde > 0:
            metric_values = list(self._get_metric_values_by_date(metric_source, metric_name).values())
            mean, std = estimate_baseline_stats(metric_values)
            if std > 0:
                experiment_in.required_sample_size = calculate_required_sample_size(
                    std=std,
                    mde=mde,
                    alpha=alpha,
                    power=power
                )
        updated = self.repo.update_experiment(experiment_id, experiment_in)
        if not updated:
            raise EntityNotFoundException(entity_name="Experiment", identifier=str(experiment_id))
        return updated

    def delete_experiment(self, experiment_id: int) -> bool:
        success = self.repo.delete_experiment(experiment_id)
        if not success:
            raise EntityNotFoundException(entity_name="Experiment", identifier=str(experiment_id))
        return True

    def list_days(self, experiment_id: int) -> List[models.ExperimentDay]:
        return self.repo.list_days(experiment_id)

    def upsert_day(self, experiment_id: int, day_in: schemas.ExperimentDayCreate) -> models.ExperimentDay:
        self.get_experiment(experiment_id)
        return self.repo.upsert_day(experiment_id, day_in)

    def delete_day(self, experiment_id: int, date_val: datetime.date) -> bool:
        success = self.repo.delete_day(experiment_id, date_val)
        if not success:
            raise EntityNotFoundException(entity_name="ExperimentDay", identifier=f"{experiment_id}/{date_val}")
        return True

    def analyze(self, experiment_id: int) -> Dict[str, Any]:
        db_exp = self.get_experiment(experiment_id)
        metric_values = self._get_metric_values_by_date(db_exp.metric_source, db_exp.metric_name)

        control_vals = []
        treatment_vals = []
        timeline = []

        if db_exp.experiment_type == "pre_post":
            for dt, val in metric_values.items():
                if dt < db_exp.start_date:
                    control_vals.append(val)
                    if dt >= db_exp.start_date - datetime.timedelta(days=30):
                        timeline.append({"date": dt.isoformat(), "value": val, "group": "Control"})
                elif dt >= db_exp.start_date:
                    if db_exp.end_date is None or dt <= db_exp.end_date:
                        treatment_vals.append(val)
                        timeline.append({"date": dt.isoformat(), "value": val, "group": "Treatment"})
        else:
            days = self.repo.list_days(experiment_id)
            control_dates = {day.date for day in days if day.group == "Control"}
            treatment_dates = {day.date for day in days if day.group == "Treatment"}

            for dt, val in metric_values.items():
                if dt in control_dates:
                    control_vals.append(val)
                    timeline.append({"date": dt.isoformat(), "value": val, "group": "Control"})
                elif dt in treatment_dates:
                    treatment_vals.append(val)
                    timeline.append({"date": dt.isoformat(), "value": val, "group": "Treatment"})

        timeline = sorted(timeline, key=lambda x: x["date"])
        analysis = analyze_experiment_data(control_vals, treatment_vals, alpha=db_exp.alpha, mde=db_exp.mde)
        analysis["timeline"] = timeline

        if db_exp.status in ["Completed", "Cancelled"] and self.db:
            cache_analysis = analysis.copy()
            if "bootstrap" in cache_analysis and "bootstrap_means_diff" in cache_analysis["bootstrap"]:
                cache_analysis["bootstrap"] = {
                    "ci_lower": cache_analysis["bootstrap"]["ci_lower"],
                    "ci_upper": cache_analysis["bootstrap"]["ci_upper"]
                }
            db_exp.results_summary = cache_analysis
            self.db.commit()

        return analysis
