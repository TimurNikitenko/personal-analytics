import io
import csv
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd

from backend.app import crud, schemas, models
from backend.app.database import get_db

router = APIRouter(
    prefix="/strength-workouts",
    tags=["Strength Workouts"]
)

@router.get("/", response_model=List[schemas.StrengthWorkout])
def read_strength_workouts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get all logged strength workouts, optionally filtered by date range.
    """
    return crud.get_strength_workouts(db, start_date=start_date, end_date=end_date)

@router.post("/", response_model=schemas.StrengthWorkout)
def create_strength_workout(
    workout: schemas.StrengthWorkoutCreate,
    db: Session = Depends(get_db)
):
    """
    Log a new strength workout with nested sets.
    """
    return crud.create_strength_workout(db, workout)

@router.delete("/{workout_id}")
def delete_strength_workout(
    workout_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a strength workout entry.
    """
    success = crud.delete_strength_workout(db, workout_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strength workout not found")
    return {"status": "success", "message": f"Workout {workout_id} deleted"}

@router.post("/import")
def import_workouts_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import strength workouts from a CSV file (e.g. exported from Strong app).
    """
    try:
        content = file.file.read().decode("utf-8")
        # Parse using pandas for convenience and robustness
        df = pd.read_csv(io.StringIO(content))
        
        # Clean column names (strip whitespace, normalize to lowercase/underscores)
        df.columns = [col.strip() for col in df.columns]
        
        # Mapping rules
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
        
        # Rename available columns
        df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})
        
        required_cols = ["date", "workout_name", "exercise_name", "set_order", "weight_kg", "reps"]
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required CSV column: {col}. Available columns: {list(df.columns)}"
                )

        # Parse date column
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by workout to create workout headers and their nested sets
        # Strong groups a single workout by Workout #, Date, Workout Name, and Duration (sec)
        group_cols = ["date", "workout_name"]
        if "workout_num" in df.columns:
            group_cols.append("workout_num")
        if "duration_seconds" in df.columns:
            group_cols.append("duration_seconds")
        if "workout_notes" in df.columns:
            group_cols.append("workout_notes")
            
        # Group by and aggregate
        workouts_created = 0
        
        # We want to identify distinct workouts. We can group by date (rounded to minute/hour) and workout_name
        # or use the full set of group cols if they don't have NaNs.
        # Let's fill NaNs for grouping:
        df_groupable = df.copy()
        if "workout_num" in df_groupable.columns:
            df_groupable["workout_num"] = df_groupable["workout_num"].fillna(1).astype(int)
        else:
            df_groupable["workout_num"] = 1
            
        if "duration_seconds" in df_groupable.columns:
            df_groupable["duration_seconds"] = df_groupable["duration_seconds"].fillna(0).astype(int)
        else:
            df_groupable["duration_seconds"] = 0
            
        if "workout_notes" in df_groupable.columns:
            df_groupable["workout_notes"] = df_groupable["workout_notes"].fillna("")
        else:
            df_groupable["workout_notes"] = ""

        # Group by date and workout name to define unique workout sessions
        grouped = df_groupable.groupby(["date", "workout_name", "workout_num", "duration_seconds", "workout_notes"])
        
        for (w_date, w_name, w_num, w_dur, w_notes), group in grouped:
            # Check if this workout already exists to prevent duplicate imports
            # Check by exact name, date, and duration
            existing = db.query(models.StrengthWorkout).filter(
                models.StrengthWorkout.date == w_date,
                models.StrengthWorkout.name == w_name
            ).first()
            
            if existing:
                continue # Skip duplicates
                
            # Create workout
            db_workout = models.StrengthWorkout(
                workout_num=int(w_num),
                date=w_date,
                name=str(w_name),
                duration_seconds=int(w_dur),
                notes=str(w_notes) if w_notes else None
            )
            db.add(db_workout)
            db.commit()
            db.refresh(db_workout)
            
            # Create sets
            for _, row in group.iterrows():
                # RPE
                rpe_val = None
                if "rpe" in row and pd.notna(row["rpe"]):
                    try:
                        rpe_val = float(row["rpe"])
                    except ValueError:
                        pass
                
                # Distance
                dist_val = None
                if "distance_meters" in row and pd.notna(row["distance_meters"]):
                    try:
                        dist_val = float(row["distance_meters"])
                    except ValueError:
                        pass
                
                # Seconds (timed exercise)
                sec_val = None
                if "seconds" in row and pd.notna(row["seconds"]):
                    try:
                        sec_val = int(row["seconds"])
                    except ValueError:
                        pass
                
                # Set notes
                notes_val = None
                if "notes" in row and pd.notna(row["notes"]):
                    notes_val = str(row["notes"]).strip()
                    if notes_val.lower() == "nan" or not notes_val:
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
                db.add(db_set)
            
            db.commit()
            workouts_created += 1
            
        return {"status": "success", "imported_count": workouts_created}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")
