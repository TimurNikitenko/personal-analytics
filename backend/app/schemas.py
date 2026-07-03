from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Any
from decimal import Decimal

# DailySupplement
class DailySupplementBase(BaseModel):
    name: str = Field(..., max_length=100)
    dosage: Decimal
    unit: str = Field(..., max_length=20)

class DailySupplementCreate(DailySupplementBase):
    pass

class DailySupplement(DailySupplementBase):
    id: int
    date: date

    class Config:
        from_attributes = True


# AgentInsight Schemas
class AgentInsightBase(BaseModel):
    date: date
    agent_question: Optional[str] = None
    user_answer: Optional[str] = None
    compiled_insight: str

class AgentInsightCreate(AgentInsightBase):
    pass

class AgentInsight(AgentInsightBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# DailyLog
class DailyLogBase(BaseModel):
    date: date
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    diary_text: Optional[str] = None
    sleep_start: Optional[datetime] = None
    sleep_end: Optional[datetime] = None
    steps: Optional[int] = Field(None, ge=0)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    workout_minutes: Optional[int] = Field(None, ge=0)
    workout_type: Optional[str] = Field(None, max_length=50)
    exercise_snacks_count: Optional[int] = Field(None, ge=0)
    work_hours: Optional[float] = Field(None, ge=0.0)

class DailyLogCreate(DailyLogBase):
    supplements: List[DailySupplementCreate] = []

class DailyLog(DailyLogBase):
    created_at: datetime
    supplements: List[DailySupplement] = []
    agent_insights: List[AgentInsight] = []

    class Config:
        from_attributes = True

# Finance
class FinanceBase(BaseModel):
    date: date
    transaction_type: str = Field(..., max_length=20) # "Expense", "Income", "Saving"
    category: str = Field(..., max_length=100)
    amount: Decimal
    description: Optional[str] = None

class FinanceCreate(FinanceBase):
    pass

class Finance(FinanceBase):
    id: int

    class Config:
        from_attributes = True

# GlobalMetric
class GlobalMetricBase(BaseModel):
    date: date
    metric_name: str = Field(..., max_length=100)
    metric_value: str = Field(..., max_length=255)
    notes: Optional[str] = None

class GlobalMetricCreate(GlobalMetricBase):
    pass

class GlobalMetric(GlobalMetricBase):
    id: int

    class Config:
        from_attributes = True

# LearningLog
class LearningLogBase(BaseModel):
    date: date
    topic: str = Field(..., max_length=255)
    learning_hours: float = Field(..., ge=0.0)
    practice_hours: float = Field(..., ge=0.0)
    notes: Optional[str] = None

class LearningLogCreate(LearningLogBase):
    pass

class LearningLog(LearningLogBase):
    id: int

    class Config:
        from_attributes = True

# Goal
class GoalBase(BaseModel):
    area: str = Field(..., max_length=50)
    description: str
    target_metric: Optional[str] = Field(None, max_length=100)
    target_value: Optional[float] = None
    start_date: date
    end_date: date
    status: str = Field(..., max_length=20) # "Active", "Completed", "Failed"
    flex_data: Optional[Any] = None

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int

    class Config:
        from_attributes = True

# DailyNutrition
class DailyNutritionBase(BaseModel):
    date: date
    water_cups: Optional[float] = None
    coffee_cups: Optional[float] = None
    coffee_type: Optional[str] = None
    caffeine_mg: Optional[float] = None
    fruits_servings: Optional[float] = None
    vegetables_servings: Optional[float] = None
    harmful_foods: Optional[str] = None

class DailyNutritionCreate(DailyNutritionBase):
    pass

class DailyNutrition(DailyNutritionBase):
    class Config:
        from_attributes = True

# MedicalTest
class MedicalTestBase(BaseModel):
    date: date
    test_name: str = Field(..., max_length=100)
    value: float
    unit: str = Field(..., max_length=50)
    reference_range: Optional[str] = Field(None, max_length=100)

class MedicalTestCreate(MedicalTestBase):
    pass

class MedicalTest(MedicalTestBase):
    id: int

    class Config:
        from_attributes = True


# Experiment Day
class ExperimentDayBase(BaseModel):
    date: date
    group: str = Field(..., max_length=20)  # "Control" or "Treatment"
    notes: Optional[str] = None

class ExperimentDayCreate(ExperimentDayBase):
    pass

class ExperimentDay(ExperimentDayBase):
    id: int
    experiment_id: int

    class Config:
        from_attributes = True


# Experiment
class ExperimentBase(BaseModel):
    title: str = Field(..., max_length=255)
    hypothesis: str
    metric_source: str = Field(..., max_length=50)
    metric_name: str = Field(..., max_length=100)
    intervention_description: str
    experiment_type: str = Field(..., max_length=50)  # "pre_post" or "randomized_days"
    start_date: date
    end_date: Optional[date] = None
    alpha: float = 0.05
    power: float = 0.80
    mde: Optional[float] = None
    required_sample_size: Optional[int] = None
    status: str = Field("Draft", max_length=20)

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(BaseModel):
    title: Optional[str] = None
    hypothesis: Optional[str] = None
    metric_source: Optional[str] = None
    metric_name: Optional[str] = None
    intervention_description: Optional[str] = None
    experiment_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    alpha: Optional[float] = None
    power: Optional[float] = None
    mde: Optional[float] = None
    required_sample_size: Optional[int] = None
    status: Optional[str] = None

class Experiment(ExperimentBase):
    id: int
    results_summary: Optional[Any] = None

    class Config:
        from_attributes = True


# === Strength Workouts Schemas ===

class WorkoutSetBase(BaseModel):
    exercise_name: str = Field(..., max_length=255)
    set_order: int = Field(..., ge=1)
    weight_kg: float = Field(..., ge=0.0)
    reps: int = Field(..., ge=0)
    rpe: Optional[float] = None
    distance_meters: Optional[float] = None
    seconds: Optional[int] = None
    notes: Optional[str] = None

class WorkoutSetCreate(WorkoutSetBase):
    pass

class WorkoutSet(WorkoutSetBase):
    id: int
    workout_id: int

    class Config:
        from_attributes = True


class StrengthWorkoutBase(BaseModel):
    workout_num: Optional[int] = None
    date: datetime
    name: str = Field(..., max_length=255)
    duration_seconds: int = Field(..., ge=0)
    notes: Optional[str] = None

class StrengthWorkoutCreate(StrengthWorkoutBase):
    sets: List[WorkoutSetCreate] = []

class StrengthWorkout(StrengthWorkoutBase):
    id: int
    sets: List[WorkoutSet] = []

    class Config:
        from_attributes = True


