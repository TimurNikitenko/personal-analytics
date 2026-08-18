"""
[DEPRECATED] Monolithic CRUD module.
Maintained for backwards compatibility. All domain operations have been refactored
into domain packages in `backend/app/domains/`.
"""

import warnings
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional, Dict, Any
from backend.app import models, schemas

from backend.app.domains.daily_logs.repository import SQLAlchemyDailyLogRepository, SQLAlchemySpontaneousNoteRepository
from backend.app.domains.daily_logs.service import DailyLogsService, NotesService
from backend.app.domains.nutrition.repository import SQLAlchemyNutritionRepository, SQLAlchemyMealRepository
from backend.app.domains.nutrition.service import NutritionService, MealService
from backend.app.domains.workouts.repository import SQLAlchemyWorkoutRepository
from backend.app.domains.workouts.service import WorkoutsService
from backend.app.domains.finances.repository import SQLAlchemyFinanceRepository
from backend.app.domains.finances.service import FinancesService
from backend.app.domains.learning.repository import SQLAlchemyLearningRepository
from backend.app.domains.learning.service import LearningService
from backend.app.domains.medical.repository import SQLAlchemyMedicalTestRepository, SQLAlchemyMetricRepository
from backend.app.domains.medical.service import MedicalTestsService, MetricsService
from backend.app.domains.goals.repository import SQLAlchemyGoalRepository
from backend.app.domains.goals.service import GoalsService
from backend.app.domains.experiments.repository import SQLAlchemyExperimentRepository
from backend.app.domains.experiments.service import ExperimentsService
from backend.app.domains.agent_insights.repository import SQLAlchemyAgentInsightRepository
from backend.app.domains.agent_insights.service import AgentInsightsService

def _warn_deprecated():
    warnings.warn(
        "backend.app.crud is deprecated. Use domain services in backend.app.domains instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Daily Logs & Notes
def get_daily_log(db: Session, log_date: date) -> Optional[models.DailyLog]:
    return SQLAlchemyDailyLogRepository(db).get_by_date(log_date)

def get_daily_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyLog]:
    return SQLAlchemyDailyLogRepository(db).list_logs(start_date=start_date, end_date=end_date)

def upsert_daily_log(db: Session, log_in: schemas.DailyLogCreate) -> models.DailyLog:
    return SQLAlchemyDailyLogRepository(db).upsert(log_in)

def delete_daily_log(db: Session, log_date: date) -> bool:
    return SQLAlchemyDailyLogRepository(db).delete(log_date)

def create_spontaneous_note(db: Session, note_in: schemas.SpontaneousNoteCreate) -> models.SpontaneousNote:
    return SQLAlchemySpontaneousNoteRepository(db).create(note_in)

def get_undisplayed_notes(db: Session) -> List[models.SpontaneousNote]:
    return SQLAlchemySpontaneousNoteRepository(db).get_undisplayed()

def get_spontaneous_notes_by_date(db: Session, target_date: date) -> List[models.SpontaneousNote]:
    return SQLAlchemySpontaneousNoteRepository(db).get_by_date(target_date)

def mark_notes_as_displayed(db: Session, note_ids: List[int]) -> bool:
    return SQLAlchemySpontaneousNoteRepository(db).mark_displayed(note_ids)

# Nutrition & Meals
def get_nutrition_log(db: Session, log_date: date) -> Optional[models.DailyNutrition]:
    return SQLAlchemyNutritionRepository(db).get_by_date(log_date)

def get_nutrition_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyNutrition]:
    return SQLAlchemyNutritionRepository(db).list_logs(start_date=start_date, end_date=end_date)

def upsert_nutrition_log(db: Session, nutrition_in: schemas.DailyNutritionCreate) -> models.DailyNutrition:
    return SQLAlchemyNutritionRepository(db).upsert(nutrition_in)

def delete_nutrition_log(db: Session, log_date: date) -> bool:
    return SQLAlchemyNutritionRepository(db).delete(log_date)

def get_food_products(db: Session) -> List[models.FoodProduct]:
    return SQLAlchemyMealRepository(db).get_food_products()

def create_food_product(db: Session, product_in: schemas.FoodProductCreate) -> models.FoodProduct:
    return SQLAlchemyMealRepository(db).create_food_product(product_in)

def get_meals_by_date(db: Session, target_date: date) -> List[models.Meal]:
    return SQLAlchemyMealRepository(db).get_by_date(target_date)

def upsert_meal(db: Session, meal_in: schemas.MealCreate) -> models.Meal:
    return SQLAlchemyMealRepository(db).upsert_meal(meal_in)

# Workouts
def get_strength_workouts(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.StrengthWorkout]:
    return SQLAlchemyWorkoutRepository(db).list_workouts(start_date=start_date, end_date=end_date)

def get_strength_workout(db: Session, workout_id: int) -> Optional[models.StrengthWorkout]:
    return SQLAlchemyWorkoutRepository(db).get_by_id(workout_id)

def create_strength_workout(db: Session, workout_in: schemas.StrengthWorkoutCreate) -> models.StrengthWorkout:
    return SQLAlchemyWorkoutRepository(db).create_workout(workout_in)

def delete_strength_workout(db: Session, workout_id: int) -> bool:
    return SQLAlchemyWorkoutRepository(db).delete_workout(workout_id)

# Finances
def get_finances(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Finance]:
    return SQLAlchemyFinanceRepository(db).list_entries(start_date=start_date, end_date=end_date)

def create_finance_entry(db: Session, finance_in: schemas.FinanceCreate) -> models.Finance:
    return SQLAlchemyFinanceRepository(db).create_entry(finance_in)

def bulk_create_finance_entries(db: Session, finance_ins: List[schemas.FinanceCreate]) -> List[models.Finance]:
    return SQLAlchemyFinanceRepository(db).bulk_create_entries(finance_ins)

def delete_finance_entry(db: Session, finance_id: int) -> bool:
    return SQLAlchemyFinanceRepository(db).delete_entry(finance_id)

# Learning
def get_learning_logs(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.LearningLog]:
    return SQLAlchemyLearningRepository(db).list_logs(start_date=start_date, end_date=end_date)

def create_learning_entry(db: Session, learning_in: schemas.LearningLogCreate) -> models.LearningLog:
    return SQLAlchemyLearningRepository(db).create_entry(learning_in)

def delete_learning_entry(db: Session, learning_id: int) -> bool:
    return SQLAlchemyLearningRepository(db).delete_entry(learning_id)

# Medical Tests & Metrics
def get_medical_tests(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None, test_name: Optional[str] = None) -> List[models.MedicalTest]:
    return SQLAlchemyMedicalTestRepository(db).list_tests(start_date=start_date, end_date=end_date, test_name=test_name)

def upsert_medical_test(db: Session, test_in: schemas.MedicalTestCreate) -> models.MedicalTest:
    return SQLAlchemyMedicalTestRepository(db).upsert_test(test_in)

def delete_medical_test(db: Session, test_id: int) -> bool:
    return SQLAlchemyMedicalTestRepository(db).delete_test(test_id)

def get_metrics(db: Session, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.GlobalMetric]:
    return SQLAlchemyMetricRepository(db).list_metrics(metric_name=metric_name, start_date=start_date, end_date=end_date)

def get_metric_names(db: Session) -> List[str]:
    return SQLAlchemyMetricRepository(db).get_metric_names()

def create_metric_entry(db: Session, metric_in: schemas.GlobalMetricCreate) -> models.GlobalMetric:
    return SQLAlchemyMetricRepository(db).create_metric(metric_in)

# Goals
def get_goals(db: Session, status: Optional[str] = None) -> List[models.Goal]:
    return SQLAlchemyGoalRepository(db).list_goals(status=status)

def create_goal(db: Session, goal_in: schemas.GoalCreate) -> models.Goal:
    return SQLAlchemyGoalRepository(db).create_goal(goal_in)

def update_goal(db: Session, goal_id: int, goal_in: schemas.GoalCreate) -> Optional[models.Goal]:
    return SQLAlchemyGoalRepository(db).update_goal(goal_id, goal_in)

def delete_goal(db: Session, goal_id: int) -> bool:
    return SQLAlchemyGoalRepository(db).delete_goal(goal_id)

# Experiments
def get_experiments(db: Session, status: Optional[str] = None) -> List[models.Experiment]:
    return SQLAlchemyExperimentRepository(db).list_experiments(status=status)

def get_experiment(db: Session, experiment_id: int) -> Optional[models.Experiment]:
    return SQLAlchemyExperimentRepository(db).get_by_id(experiment_id)

def create_experiment(db: Session, experiment_in: schemas.ExperimentCreate) -> models.Experiment:
    return SQLAlchemyExperimentRepository(db).create_experiment(experiment_in)

def update_experiment(db: Session, experiment_id: int, experiment_in: schemas.ExperimentUpdate) -> Optional[models.Experiment]:
    return SQLAlchemyExperimentRepository(db).update_experiment(experiment_id, experiment_in)

def delete_experiment(db: Session, experiment_id: int) -> bool:
    return SQLAlchemyExperimentRepository(db).delete_experiment(experiment_id)

def get_experiment_days(db: Session, experiment_id: int) -> List[models.ExperimentDay]:
    return SQLAlchemyExperimentRepository(db).list_days(experiment_id)

def upsert_experiment_day(db: Session, experiment_id: int, day_in: schemas.ExperimentDayCreate) -> models.ExperimentDay:
    return SQLAlchemyExperimentRepository(db).upsert_day(experiment_id, day_in)

def delete_experiment_day(db: Session, experiment_id: int, date_val: date) -> bool:
    return SQLAlchemyExperimentRepository(db).delete_day(experiment_id, date_val)

# Agent Insights
def get_agent_insights(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.AgentInsight]:
    return SQLAlchemyAgentInsightRepository(db).list_insights(start_date=start_date, end_date=end_date)

def create_agent_insight(db: Session, insight_in: schemas.AgentInsightCreate) -> models.AgentInsight:
    return SQLAlchemyAgentInsightRepository(db).create_insight(insight_in)

def delete_agent_insight(db: Session, insight_id: int) -> bool:
    return SQLAlchemyAgentInsightRepository(db).delete_insight(insight_id)
