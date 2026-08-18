"""
Domain Application Service for Strength Workouts.
Contains workout volume calculation, 1RM estimates, CSV import logic, and CRUD operations.
"""

import io
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException, ValidationErrorException
from backend.app.domains.workouts.interfaces import IWorkoutRepository

class WorkoutsService:
    def __init__(self, repo: IWorkoutRepository, db: Optional[Session] = None):
        self.repo = repo
        self.db = db

    def list_workouts(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.StrengthWorkout]:
        return self.repo.list_workouts(start_date=start_date, end_date=end_date)

    def get_workout(self, workout_id: int) -> models.StrengthWorkout:
        workout = self.repo.get_by_id(workout_id)
        if not workout:
            raise EntityNotFoundException(entity_name="StrengthWorkout", identifier=str(workout_id))
        return workout

    def create_workout(self, workout_in: schemas.StrengthWorkoutCreate) -> models.StrengthWorkout:
        return self.repo.create_workout(workout_in)

    def delete_workout(self, workout_id: int) -> bool:
        success = self.repo.delete_workout(workout_id)
        if not success:
            raise EntityNotFoundException(entity_name="StrengthWorkout", identifier=str(workout_id))
        return True

    @staticmethod
    def calculate_one_rep_max(weight_kg: float, reps: int) -> float:
        """Calculate estimated 1RM using Epley formula."""
        if reps <= 0 or weight_kg <= 0:
            return 0.0
        if reps == 1:
            return weight_kg
        return round(weight_kg * (1 + reps / 30.0), 2)

    def import_csv(self, file_content: bytes) -> Dict[str, Any]:
        """Import workouts from Strong app CSV file."""
        if not self.db:
            raise ValidationErrorException("Database session required for CSV import.")

        try:
            content = file_content.decode("utf-8")
            df = pd.read_csv(io.StringIO(content))
            df.columns = [col.strip() for col in df.columns]

            col_mapping = {
                "Workout #": "workout_num",
                "Date": "date",
                "Workout Name": "workout_name",
                "Duration (sec)": "duration_seconds",
                "Exercise Name": "exercise_name",
                "Set Order": "set_order",
                "Weight (kg)": "weight_kg",
                "Reps": "reps",
                "RPE": "rpe",
                "Distance (meters)": "distance_meters",
                "Seconds": "seconds",
                "Notes": "notes",
                "Workout Notes": "workout_notes"
            }
            df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})

            required_cols = ["date", "workout_name", "exercise_name", "set_order", "weight_kg", "reps"]
            for col in required_cols:
                if col not in df.columns:
                    raise ValidationErrorException(f"Missing required CSV column: {col}")

            df['date'] = pd.to_datetime(df['date'])

            df_groupable = df.copy()
            df_groupable["workout_num"] = df_groupable["workout_num"].fillna(1).astype(int) if "workout_num" in df_groupable.columns else 1
            df_groupable["duration_seconds"] = df_groupable["duration_seconds"].fillna(0).astype(int) if "duration_seconds" in df_groupable.columns else 0
            df_groupable["workout_notes"] = df_groupable["workout_notes"].fillna("") if "workout_notes" in df_groupable.columns else ""

            grouped = df_groupable.groupby(["date", "workout_name", "workout_num", "duration_seconds", "workout_notes"])
            workouts_created = 0

            for (w_date, w_name, w_num, w_dur, w_notes), group in grouped:
                existing = self.db.query(models.StrengthWorkout).filter(
                    models.StrengthWorkout.date == w_date,
                    models.StrengthWorkout.name == w_name
                ).first()
                if existing:
                    continue

                db_workout = models.StrengthWorkout(
                    workout_num=int(w_num),
                    date=w_date,
                    name=str(w_name),
                    duration_seconds=int(w_dur),
                    notes=str(w_notes) if w_notes else None
                )
                self.db.add(db_workout)
                self.db.commit()
                self.db.refresh(db_workout)

                for _, row in group.iterrows():
                    rpe_val = float(row["rpe"]) if "rpe" in row and pd.notna(row["rpe"]) else None
                    dist_val = float(row["distance_meters"]) if "distance_meters" in row and pd.notna(row["distance_meters"]) else None
                    sec_val = int(row["seconds"]) if "seconds" in row and pd.notna(row["seconds"]) else None
                    notes_val = str(row["notes"]).strip() if "notes" in row and pd.notna(row["notes"]) else None
                    if notes_val and notes_val.lower() == "nan":
                        notes_val = None

                    db_set = models.WorkoutSet(
                        workout_id=db_workout.id,
                        exercise_name=str(row["exercise_name"]),
                        set_order=int(row["set_order"]),
                        weight_kg=float(row["weight_kg"]),
                        reps=int(row["reps"]),
                        rpe=rpe_val,
                        distance_meters=dist_val,
                        seconds=sec_val,
                        notes=notes_val
                    )
                    self.db.add(db_set)

                self.db.commit()
                workouts_created += 1

            return {"status": "success", "imported_count": workouts_created}
        except ValidationErrorException as ve:
            raise ve
        except Exception as e:
            raise ValidationErrorException(f"Failed to process CSV file: {str(e)}")
