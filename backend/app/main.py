import io
import zipfile
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.database import engine, Base, get_db
from backend.app.routers import daily_logs, finances, metrics, learning, goals, ml, telegram, nutrition, medical_tests, experiments, strength_workouts

# Auto-create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Analytics API", version="1.0.0")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(daily_logs.router, prefix="/api")
app.include_router(finances.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(goals.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")
app.include_router(nutrition.router, prefix="/api")
app.include_router(medical_tests.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(strength_workouts.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Personal Analytics Backend"}

@app.get("/api/export")
def export_data(db: Session = Depends(get_db)):
    """
    Exports all database tables as a ZIP file containing individual CSV files.
    """
    # Define SQL queries to pull data
    queries = {
        "daily_logs.csv": "SELECT * FROM daily_logs ORDER BY date DESC",
        "daily_supplements.csv": "SELECT * FROM daily_supplements ORDER BY date DESC, name ASC",
        "finances.csv": "SELECT * FROM finances ORDER BY date DESC",
        "global_metrics.csv": "SELECT * FROM global_metrics ORDER BY date DESC",
        "learning_logs.csv": "SELECT * FROM learning_logs ORDER BY date DESC",
        "goals.csv": "SELECT * FROM goals ORDER BY end_date ASC",
        "daily_nutrition.csv": "SELECT * FROM daily_nutrition ORDER BY date DESC",
        "medical_tests.csv": "SELECT * FROM medical_tests ORDER BY date DESC, test_name ASC",
        "strength_workouts.csv": "SELECT * FROM strength_workouts ORDER BY date DESC",
        "strength_workout_sets.csv": "SELECT * FROM strength_workout_sets ORDER BY workout_id ASC, set_order ASC"
    }

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, sql in queries.items():
            df = pd.read_sql_query(sql, con=engine)
            csv_data = df.to_csv(index=False)
            zip_file.writestr(file_name, csv_data)

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=personal_analytics_export.zip"}
    )


@app.post("/api/backup")
def run_backup():
    """
    Triggers pg_dump on the database and stores the SQL dump in /app/backups.
    """
    import os
    import subprocess
    from datetime import datetime
    from fastapi import HTTPException
    
    backup_dir = "/app/backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    filepath = os.path.join(backup_dir, filename)
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@db:5432/personal_analytics")
    
    try:
        result = subprocess.run(
            ["pg_dump", db_url, "-f", filepath],
            check=True,
            capture_output=True,
            text=True
        )
        return {"status": "success", "backup_file": filename}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database backup failed: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup error: {str(e)}"
        )

