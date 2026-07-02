from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import models, schemas

# ==================== Daily Logs & Supplements ====================

def get_daily_log(db: Session, log_date: date) -> Optional[models.DailyLog]:
    return db.query(models.DailyLog).filter(models.DailyLog.date == log_date).first()

def get_daily_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyLog]:
    query = db.query(models.DailyLog)
    if start_date:
        query = query.filter(models.DailyLog.date >= start_date)
    if end_date:
        query = query.filter(models.DailyLog.date <= end_date)
    return query.order_by(models.DailyLog.date.desc()).all()

def upsert_daily_log(db: Session, log_in: schemas.DailyLogCreate) -> models.DailyLog:
    db_log = get_daily_log(db, log_in.date)
    
    log_data = log_in.model_dump(exclude={"supplements"})
    
    if db_log:
        # Update existing
        for key, value in log_data.items():
            setattr(db_log, key, value)
    else:
        # Create new
        db_log = models.DailyLog(**log_data)
        db.add(db_log)
    
    db.commit()
    db.refresh(db_log)
    
    # Handle supplements: delete old ones for this date and add new ones
    db.query(models.DailySupplement).filter(models.DailySupplement.date == log_in.date).delete()
    
    for supp_in in log_in.supplements:
        db_supp = models.DailySupplement(
            date=log_in.date,
            name=supp_in.name,
            dosage=supp_in.dosage,
            unit=supp_in.unit
        )
        db.add(db_supp)
        
    db.commit()
    db.refresh(db_log)
    return db_log

def delete_daily_log(db: Session, log_date: date) -> bool:
    db_log = get_daily_log(db, log_date)
    if db_log:
        db.delete(db_log)
        db.commit()
        return True
    return False

# ==================== Finances ====================

def create_finance_entry(db: Session, finance_in: schemas.FinanceCreate) -> models.Finance:
    db_finance = models.Finance(**finance_in.model_dump())
    db.add(db_finance)
    db.commit()
    db.refresh(db_finance)
    return db_finance

def bulk_create_finance_entries(db: Session, finance_ins: List[schemas.FinanceCreate]) -> List[models.Finance]:
    db_entries = [models.Finance(**entry.model_dump()) for entry in finance_ins]
    db.add_all(db_entries)
    db.commit()
    return db_entries

def get_finances(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Finance]:
    query = db.query(models.Finance)
    if start_date:
        query = query.filter(models.Finance.date >= start_date)
    if end_date:
        query = query.filter(models.Finance.date <= end_date)
    return query.order_by(models.Finance.date.desc()).all()

def delete_finance_entry(db: Session, finance_id: int) -> bool:
    db_finance = db.query(models.Finance).filter(models.Finance.id == finance_id).first()
    if db_finance:
        db.delete(db_finance)
        db.commit()
        return True
    return False

# ==================== Global Metrics ====================

def create_metric_entry(db: Session, metric_in: schemas.GlobalMetricCreate) -> models.GlobalMetric:
    db_metric = db.query(models.GlobalMetric).filter(
        models.GlobalMetric.date == metric_in.date,
        models.GlobalMetric.metric_name == metric_in.metric_name
    ).first()
    
    if db_metric:
        db_metric.metric_value = metric_in.metric_value
        db_metric.notes = metric_in.notes
    else:
        db_metric = models.GlobalMetric(**metric_in.model_dump())
        db.add(db_metric)
        
    db.commit()
    db.refresh(db_metric)
    return db_metric

def get_metrics(db: Session, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.GlobalMetric]:
    query = db.query(models.GlobalMetric)
    if metric_name:
        query = query.filter(models.GlobalMetric.metric_name == metric_name)
    if start_date:
        query = query.filter(models.GlobalMetric.date >= start_date)
    if end_date:
        query = query.filter(models.GlobalMetric.date <= end_date)
    return query.order_by(models.GlobalMetric.date.desc()).all()

def get_metric_names(db: Session) -> List[str]:
    results = db.query(models.GlobalMetric.metric_name).distinct().all()
    return [r[0] for r in results]

# ==================== Learning Logs ====================

def create_learning_entry(db: Session, learning_in: schemas.LearningLogCreate) -> models.LearningLog:
    db_learning = models.LearningLog(**learning_in.model_dump())
    db.add(db_learning)
    db.commit()
    db.refresh(db_learning)
    return db_learning

def get_learning_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.LearningLog]:
    query = db.query(models.LearningLog)
    if start_date:
        query = query.filter(models.LearningLog.date >= start_date)
    if end_date:
        query = query.filter(models.LearningLog.date <= end_date)
    return query.order_by(models.LearningLog.date.desc()).all()

def delete_learning_entry(db: Session, learning_id: int) -> bool:
    db_learning = db.query(models.LearningLog).filter(models.LearningLog.id == learning_id).first()
    if db_learning:
        db.delete(db_learning)
        db.commit()
        return True
    return False

# ==================== Goals ====================

def create_goal(db: Session, goal_in: schemas.GoalCreate) -> models.Goal:
    db_goal = models.Goal(**goal_in.model_dump())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_goals(db: Session, status: Optional[str] = None) -> List[models.Goal]:
    query = db.query(models.Goal)
    if status:
        query = query.filter(models.Goal.status == status)
    return query.order_by(models.Goal.end_date.asc()).all()

def update_goal(db: Session, goal_id: int, goal_in: schemas.GoalCreate) -> Optional[models.Goal]:
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if db_goal:
        for key, value in goal_in.model_dump().items():
            setattr(db_goal, key, value)
        db.commit()
        db.refresh(db_goal)
        return db_goal
    return None

def delete_goal(db: Session, goal_id: int) -> bool:
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if db_goal:
        db.delete(db_goal)
        db.commit()
        return True
    return False

# ==================== Nutrition ====================

def get_nutrition_log(db: Session, log_date: date) -> Optional[models.DailyNutrition]:
    return db.query(models.DailyNutrition).filter(models.DailyNutrition.date == log_date).first()

def get_nutrition_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyNutrition]:
    query = db.query(models.DailyNutrition)
    if start_date:
        query = query.filter(models.DailyNutrition.date >= start_date)
    if end_date:
        query = query.filter(models.DailyNutrition.date <= end_date)
    return query.order_by(models.DailyNutrition.date.desc()).all()

def upsert_nutrition_log(db: Session, nutrition_in: schemas.DailyNutritionCreate) -> models.DailyNutrition:
    db_nut = get_nutrition_log(db, nutrition_in.date)
    
    nut_data = nutrition_in.model_dump()
    
    # Auto-calculate caffeine
    cups = nut_data.get("coffee_cups") or 0.0
    coffee_type = nut_data.get("coffee_type") or "Filter"
    mapping = {
        "Espresso": 63.0,
        "Filter": 95.0,
        "Instant": 63.0,
        "Decaf": 3.0
    }
    nut_data["caffeine_mg"] = cups * mapping.get(coffee_type, 95.0)

    if db_nut:
        for key, value in nut_data.items():
            setattr(db_nut, key, value)
    else:
        db_nut = models.DailyNutrition(**nut_data)
        db.add(db_nut)
        
    db.commit()
    db.refresh(db_nut)
    return db_nut

def delete_nutrition_log(db: Session, log_date: date) -> bool:
    db_nut = get_nutrition_log(db, log_date)
    if db_nut:
        db.delete(db_nut)
        db.commit()
        return True
    return False

# ==================== Medical Tests ====================

def get_medical_tests(
    db: Session, 
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    test_name: Optional[str] = None
) -> List[models.MedicalTest]:
    query = db.query(models.MedicalTest)
    if start_date:
        query = query.filter(models.MedicalTest.date >= start_date)
    if end_date:
        query = query.filter(models.MedicalTest.date <= end_date)
    if test_name:
        query = query.filter(models.MedicalTest.test_name == test_name)
    return query.order_by(models.MedicalTest.date.desc(), models.MedicalTest.test_name.asc()).all()

def upsert_medical_test(db: Session, test_in: schemas.MedicalTestCreate) -> models.MedicalTest:
    db_test = db.query(models.MedicalTest).filter(
        models.MedicalTest.date == test_in.date,
        models.MedicalTest.test_name == test_in.test_name
    ).first()
    
    test_data = test_in.model_dump()
    
    if db_test:
        for key, value in test_data.items():
            setattr(db_test, key, value)
    else:
        db_test = models.MedicalTest(**test_data)
        db.add(db_test)
        
    db.commit()
    db.refresh(db_test)
    return db_test

def delete_medical_test(db: Session, test_id: int) -> bool:
    db_test = db.query(models.MedicalTest).filter(models.MedicalTest.id == test_id).first()
    if db_test:
        db.delete(db_test)
        db.commit()
        return True
    return False


# ==================== Experiments ====================

def create_experiment(db: Session, experiment_in: schemas.ExperimentCreate) -> models.Experiment:
    db_experiment = models.Experiment(**experiment_in.model_dump())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment

def get_experiment(db: Session, experiment_id: int) -> Optional[models.Experiment]:
    return db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()

def get_experiments(db: Session, status: Optional[str] = None) -> List[models.Experiment]:
    query = db.query(models.Experiment)
    if status:
        query = query.filter(models.Experiment.status == status)
    return query.order_by(models.Experiment.start_date.desc()).all()

def update_experiment(db: Session, experiment_id: int, experiment_in: schemas.ExperimentUpdate) -> Optional[models.Experiment]:
    db_experiment = get_experiment(db, experiment_id)
    if db_experiment:
        update_data = experiment_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_experiment, key, value)
        db.commit()
        db.refresh(db_experiment)
        return db_experiment
    return None

def delete_experiment(db: Session, experiment_id: int) -> bool:
    db_experiment = get_experiment(db, experiment_id)
    if db_experiment:
        db.delete(db_experiment)
        db.commit()
        return True
    return False

# ==================== Experiment Days ====================

def upsert_experiment_day(db: Session, experiment_id: int, day_in: schemas.ExperimentDayCreate) -> models.ExperimentDay:
    db_day = db.query(models.ExperimentDay).filter(
        models.ExperimentDay.experiment_id == experiment_id,
        models.ExperimentDay.date == day_in.date
    ).first()
    
    day_data = day_in.model_dump()
    day_data["experiment_id"] = experiment_id
    
    if db_day:
        for key, value in day_data.items():
            setattr(db_day, key, value)
    else:
        db_day = models.ExperimentDay(**day_data)
        db.add(db_day)
        
    db.commit()
    db.refresh(db_day)
    return db_day

def get_experiment_days(db: Session, experiment_id: int) -> List[models.ExperimentDay]:
    return db.query(models.ExperimentDay).filter(
        models.ExperimentDay.experiment_id == experiment_id
    ).order_by(models.ExperimentDay.date.asc()).all()

def delete_experiment_day(db: Session, experiment_id: int, date_val: date) -> bool:
    db_day = db.query(models.ExperimentDay).filter(
        models.ExperimentDay.experiment_id == experiment_id,
        models.ExperimentDay.date == date_val
    ).first()
    if db_day:
        db.delete(db_day)
        db.commit()
        return True
    return False


# ==================== Strength Workouts ====================

def get_strength_workout(db: Session, workout_id: int) -> Optional[models.StrengthWorkout]:
    return db.query(models.StrengthWorkout).filter(models.StrengthWorkout.id == workout_id).first()

def get_strength_workouts(
    db: Session, 
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None
) -> List[models.StrengthWorkout]:
    query = db.query(models.StrengthWorkout)
    if start_date:
        query = query.filter(models.StrengthWorkout.date >= start_date)
    if end_date:
        from datetime import datetime, time
        end_dt = datetime.combine(end_date, time(23, 59, 59))
        query = query.filter(models.StrengthWorkout.date <= end_dt)
    return query.order_by(models.StrengthWorkout.date.desc()).all()

def create_strength_workout(db: Session, workout_in: schemas.StrengthWorkoutCreate) -> models.StrengthWorkout:
    db_workout = models.StrengthWorkout(
        workout_num=workout_in.workout_num,
        date=workout_in.date,
        name=workout_in.name,
        duration_seconds=workout_in.duration_seconds,
        notes=workout_in.notes
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)

    for set_in in workout_in.sets:
        db_set = models.WorkoutSet(
            workout_id=db_workout.id,
            exercise_name=set_in.exercise_name,
            set_order=set_in.set_order,
            weight_kg=set_in.weight_kg,
            reps=set_in.reps,
            rpe=set_in.rpe,
            distance_meters=set_in.distance_meters,
            seconds=set_in.seconds,
            notes=set_in.notes
        )
        db.add(db_set)

    db.commit()
    db.refresh(db_workout)
    return db_workout

def delete_strength_workout(db: Session, workout_id: int) -> bool:
    db_workout = get_strength_workout(db, workout_id)
    if db_workout:
        db.delete(db_workout)
        db.commit()
        return True
    return False


