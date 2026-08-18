"""
SQLAlchemy repository implementation for Strength Workouts.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.workouts.interfaces import IWorkoutRepository

class SQLAlchemyWorkoutRepository(IWorkoutRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_workouts(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.StrengthWorkout]:
        query = self.db.query(models.StrengthWorkout)
        if start_date:
            query = query.filter(models.StrengthWorkout.date >= start_date)
        if end_date:
            query = query.filter(models.StrengthWorkout.date <= end_date)
        return query.order_by(models.StrengthWorkout.date.desc()).all()

    def get_by_id(self, workout_id: int) -> Optional[models.StrengthWorkout]:
        return self.db.query(models.StrengthWorkout).filter(models.StrengthWorkout.id == workout_id).first()

    def create_workout(self, workout_in: schemas.StrengthWorkoutCreate) -> models.StrengthWorkout:
        db_workout = models.StrengthWorkout(
            workout_num=workout_in.workout_num,
            date=workout_in.date,
            name=workout_in.name,
            duration_seconds=workout_in.duration_seconds,
            notes=workout_in.notes
        )
        self.db.add(db_workout)
        self.db.commit()
        self.db.refresh(db_workout)

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
            self.db.add(db_set)

        self.db.commit()
        self.db.refresh(db_workout)
        return db_workout

    def delete_workout(self, workout_id: int) -> bool:
        db_workout = self.get_by_id(workout_id)
        if db_workout:
            self.db.delete(db_workout)
            self.db.commit()
            return True
        return False
