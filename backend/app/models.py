from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Numeric, ForeignKey, text, UniqueConstraint, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from backend.app.database import Base

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

class DailyLog(Base):
    __tablename__ = "daily_logs"

    date = Column(Date, primary_key=True)
    mood_score = Column(Integer, nullable=True)
    diary_text = Column(String, nullable=True)
    sleep_start = Column(DateTime(timezone=True), nullable=True)
    sleep_end = Column(DateTime(timezone=True), nullable=True)
    steps = Column(Integer, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    workout_minutes = Column(Integer, nullable=True)
    workout_type = Column(String(50), nullable=True)
    exercise_snacks_count = Column(Integer, nullable=True)
    work_hours = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    supplements = relationship("DailySupplement", back_populates="daily_log", cascade="all, delete-orphan")
    agent_insights = relationship("AgentInsight", back_populates="daily_log", cascade="all, delete-orphan")

class DailySupplement(Base):
    __tablename__ = "daily_supplements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, ForeignKey("daily_logs.date", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    dosage = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)

    daily_log = relationship("DailyLog", back_populates="supplements")

class Finance(Base):
    __tablename__ = "finances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    transaction_type = Column(String(20), nullable=False) # "Expense", "Income", "Saving"
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=True)

class GlobalMetric(Base):
    __tablename__ = "global_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    metric_name = Column(String(100), nullable=False) # e.g. "VO2Max", "HRV", "Weight"
    metric_value = Column(String(255), nullable=False)
    notes = Column(String, nullable=True)

class LearningLog(Base):
    __tablename__ = "learning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    topic = Column(String(255), nullable=False)
    learning_hours = Column(Float, nullable=False)
    practice_hours = Column(Float, nullable=False)
    notes = Column(String, nullable=True)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    area = Column(String(50), nullable=False) # "Physical", "Finances", "Learning", etc.
    description = Column(String, nullable=False)
    target_metric = Column(String(100), nullable=True)
    target_value = Column(Float, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False) # "Active", "Completed", "Failed"
    flex_data = Column(JSONB, nullable=True)

class DailyNutrition(Base):
    __tablename__ = "daily_nutrition"

    date = Column(Date, primary_key=True)
    water_cups = Column(Float, nullable=True)
    coffee_cups = Column(Float, nullable=True)
    coffee_type = Column(String(50), nullable=True)
    caffeine_mg = Column(Float, nullable=True)
    fruits_servings = Column(Float, nullable=True)
    vegetables_servings = Column(Float, nullable=True)
    harmful_foods = Column(String, nullable=True)

class MedicalTest(Base):
    __tablename__ = "medical_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    test_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    reference_range = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "test_name", name="uq_date_test"),
    )


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(255), nullable=False)


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    hypothesis = Column(String, nullable=False)
    metric_source = Column(String(50), nullable=False)  # "daily_logs", "global_metrics", "learning_logs", "daily_nutrition", "medical_tests"
    metric_name = Column(String(100), nullable=False)
    intervention_description = Column(String, nullable=False)
    experiment_type = Column(String(50), nullable=False)  # "pre_post" or "randomized_days"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    alpha = Column(Float, default=0.05)
    power = Column(Float, default=0.80)
    mde = Column(Float, nullable=True)
    required_sample_size = Column(Integer, nullable=True)
    status = Column(String(20), default="Draft")  # "Draft", "Active", "Completed", "Cancelled"
    results_summary = Column(JSONB, nullable=True)

    days = relationship("ExperimentDay", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentDay(Base):
    __tablename__ = "experiment_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    group = Column(String(20), nullable=False)  # "Control" or "Treatment"
    notes = Column(String, nullable=True)

    experiment = relationship("Experiment", back_populates="days")

    __table_args__ = (
        UniqueConstraint("experiment_id", "date", name="uq_experiment_date"),
    )


class StrengthWorkout(Base):
    __tablename__ = "strength_workouts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_num = Column(Integer, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    name = Column(String(255), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    notes = Column(String, nullable=True)

    sets = relationship("WorkoutSet", back_populates="workout", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "strength_workout_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_id = Column(Integer, ForeignKey("strength_workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_name = Column(String(255), nullable=False)
    set_order = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    rpe = Column(Float, nullable=True)
    distance_meters = Column(Float, nullable=True)
    seconds = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    workout = relationship("StrengthWorkout", back_populates="sets")


class AgentInsight(Base):
    __tablename__ = "agent_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, ForeignKey("daily_logs.date", ondelete="CASCADE"), nullable=False)
    agent_question = Column(String, nullable=True)
    user_answer = Column(String, nullable=True)
    compiled_insight = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    daily_log = relationship("DailyLog", back_populates="agent_insights")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)  # "Breakfast", "Lunch", "Dinner"
    photo_path = Column(String, nullable=True)

    items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("date", "meal_type", name="uq_date_meal_type"),
    )

class MealItem(Base):
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)

    meal = relationship("Meal", back_populates="items")

class FoodProduct(Base):
    __tablename__ = "food_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    default_unit = Column(String(50), nullable=False, default="грамм")

class SpontaneousNote(Base):
    __tablename__ = "spontaneous_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    note_text = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_type = Column(String(20), nullable=False, default="text")  # "text", "voice", "image", "video"
    displayed = Column(Boolean, default=False, nullable=False)


