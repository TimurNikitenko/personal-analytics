import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.app import schemas, crud
from backend.app.database import get_db
from backend.app.utils.statistics import (
    analyze_experiment_data,
    calculate_required_sample_size,
    estimate_baseline_stats
)

router = APIRouter(prefix="/experiments", tags=["Experiments"])

def get_metric_values_by_date(db: Session, metric_source: str, metric_name: str) -> Dict[datetime.date, float]:
    """
    Helper to extract all date -> value pairs for a given metric.
    """
    res = {}
    if metric_source == "daily_logs":
        logs = crud.get_daily_logs(db)
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
        metrics = crud.get_metrics(db, metric_name=metric_name)
        for m in metrics:
            try:
                res[m.date] = float(m.metric_value)
            except ValueError:
                pass
                
    elif metric_source == "learning_logs":
        logs = crud.get_learning_logs(db)
        for log in logs:
            val = None
            if metric_name == "total_hours":
                val = log.learning_hours + log.practice_hours
            else:
                val = getattr(log, metric_name, None)
            if val is not None:
                res[log.date] = float(val)
                
    elif metric_source == "daily_nutrition":
        logs = crud.get_nutrition_logs(db)
        for log in logs:
            val = getattr(log, metric_name, None)
            if val is not None:
                res[log.date] = float(val)
                
    elif metric_source == "medical_tests":
        tests = crud.get_medical_tests(db, test_name=metric_name)
        for t in tests:
            res[t.date] = float(t.value)
            
    return res

@router.get("/", response_model=List[schemas.Experiment])
@router.get("", response_model=List[schemas.Experiment])
def read_experiments(status: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_experiments(db, status=status)

@router.get("/{experiment_id}", response_model=schemas.Experiment)
def read_experiment(experiment_id: int, db: Session = Depends(get_db)):
    db_exp = crud.get_experiment(db, experiment_id)
    if not db_exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_exp

@router.post("/", response_model=schemas.Experiment)
@router.post("", response_model=schemas.Experiment)
def create_experiment(experiment_in: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    # Automatically compute required sample size if MDE and baseline stats are available
    if experiment_in.mde and experiment_in.mde > 0:
        metric_values = list(get_metric_values_by_date(db, experiment_in.metric_source, experiment_in.metric_name).values())
        mean, std = estimate_baseline_stats(metric_values)
        if std > 0:
            experiment_in.required_sample_size = calculate_required_sample_size(
                std=std,
                mde=experiment_in.mde,
                alpha=experiment_in.alpha,
                power=experiment_in.power
            )
    return crud.create_experiment(db, experiment_in=experiment_in)

@router.put("/{experiment_id}", response_model=schemas.Experiment)
def update_experiment(experiment_id: int, experiment_in: schemas.ExperimentUpdate, db: Session = Depends(get_db)):
    # Recalculate required sample size if parameters change
    db_exp = crud.get_experiment(db, experiment_id)
    if not db_exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    mde = experiment_in.mde if experiment_in.mde is not None else db_exp.mde
    alpha = experiment_in.alpha if experiment_in.alpha is not None else db_exp.alpha
    power = experiment_in.power if experiment_in.power is not None else db_exp.power
    metric_source = experiment_in.metric_source if experiment_in.metric_source is not None else db_exp.metric_source
    metric_name = experiment_in.metric_name if experiment_in.metric_name is not None else db_exp.metric_name
    
    if mde and mde > 0:
        metric_values = list(get_metric_values_by_date(db, metric_source, metric_name).values())
        mean, std = estimate_baseline_stats(metric_values)
        if std > 0:
            experiment_in.required_sample_size = calculate_required_sample_size(
                std=std,
                mde=mde,
                alpha=alpha,
                power=power
            )

    updated_exp = crud.update_experiment(db, experiment_id=experiment_id, experiment_in=experiment_in)
    return updated_exp

@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    success = crud.delete_experiment(db, experiment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"status": "success", "detail": "Experiment deleted"}

# === Experiment Days Logging ===

@router.get("/{experiment_id}/days", response_model=List[schemas.ExperimentDay])
def read_experiment_days(experiment_id: int, db: Session = Depends(get_db)):
    return crud.get_experiment_days(db, experiment_id=experiment_id)

@router.post("/{experiment_id}/days", response_model=schemas.ExperimentDay)
def log_experiment_day(experiment_id: int, day_in: schemas.ExperimentDayCreate, db: Session = Depends(get_db)):
    db_exp = crud.get_experiment(db, experiment_id)
    if not db_exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return crud.upsert_experiment_day(db, experiment_id=experiment_id, day_in=day_in)

@router.delete("/{experiment_id}/days/{date_str}")
def delete_experiment_day(experiment_id: int, date_str: str, db: Session = Depends(get_db)):
    try:
        date_val = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
    success = crud.delete_experiment_day(db, experiment_id=experiment_id, date_val=date_val)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment day entry not found")
    return {"status": "success", "detail": "Experiment day deleted"}

# === Statistical Analysis and Planning Helpers ===

@router.get("/{experiment_id}/analyze")
def analyze_experiment(experiment_id: int, db: Session = Depends(get_db)):
    db_exp = crud.get_experiment(db, experiment_id)
    if not db_exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    # Get all metric values by date
    metric_values = get_metric_values_by_date(db, db_exp.metric_source, db_exp.metric_name)
    
    control_vals = []
    treatment_vals = []
    timeline = []
    
    if db_exp.experiment_type == "pre_post":
        for dt, val in metric_values.items():
            if dt < db_exp.start_date:
                control_vals.append(val)
                # Keep timeline reasonably clean (last 30 days of control)
                if dt >= db_exp.start_date - datetime.timedelta(days=30):
                    timeline.append({
                        "date": dt.isoformat(),
                        "value": val,
                        "group": "Control"
                    })
            elif dt >= db_exp.start_date:
                if db_exp.end_date is None or dt <= db_exp.end_date:
                    treatment_vals.append(val)
                    timeline.append({
                        "date": dt.isoformat(),
                        "value": val,
                        "group": "Treatment"
                    })
    else:
        # randomized_days
        days = crud.get_experiment_days(db, experiment_id)
        control_dates = {day.date for day in days if day.group == "Control"}
        treatment_dates = {day.date for day in days if day.group == "Treatment"}
        
        for dt, val in metric_values.items():
            if dt in control_dates:
                control_vals.append(val)
                timeline.append({
                    "date": dt.isoformat(),
                    "value": val,
                    "group": "Control"
                })
            elif dt in treatment_dates:
                treatment_vals.append(val)
                timeline.append({
                    "date": dt.isoformat(),
                    "value": val,
                    "group": "Treatment"
                })
                
    # Sort timeline chronologically
    timeline = sorted(timeline, key=lambda x: x["date"])
    
    analysis = analyze_experiment_data(control_vals, treatment_vals, alpha=db_exp.alpha, mde=db_exp.mde)
    analysis["timeline"] = timeline
    
    # Cache results in DB if experiment is Completed or Cancelled
    if db_exp.status in ["Completed", "Cancelled"]:
        # Exclude bootstrap distribution from cached results to avoid bloating DB
        cache_analysis = analysis.copy()
        if "bootstrap" in cache_analysis and "bootstrap_means_diff" in cache_analysis["bootstrap"]:
            cache_analysis["bootstrap"] = {
                "ci_lower": cache_analysis["bootstrap"]["ci_lower"],
                "ci_upper": cache_analysis["bootstrap"]["ci_upper"]
            }
        db_exp.results_summary = cache_analysis
        db.commit()
        
    return analysis

@router.get("/helpers/baseline-stats")
def get_metric_baseline_stats(metric_source: str, metric_name: str, db: Session = Depends(get_db)):
    """
    Retrieves baseline mean and std for a chosen metric to assist in planning.
    """
    metric_values = list(get_metric_values_by_date(db, metric_source, metric_name).values())
    if not metric_values:
        return {"n": 0, "mean": 0.0, "std": 0.0}
        
    mean, std = estimate_baseline_stats(metric_values)
    return {"n": len(metric_values), "mean": mean, "std": std}
