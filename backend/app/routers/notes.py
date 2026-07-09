from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/notes", tags=["Spontaneous Notes"])

@router.post("/", response_model=schemas.SpontaneousNote)
@router.post("", response_model=schemas.SpontaneousNote)
def create_note(note_in: schemas.SpontaneousNoteCreate, db: Session = Depends(get_db)):
    return crud.create_spontaneous_note(db, note_in=note_in)

@router.get("/undisplayed", response_model=List[schemas.SpontaneousNote])
def get_undisplayed_notes(db: Session = Depends(get_db)):
    return crud.get_undisplayed_notes(db)

@router.get("/by-date", response_model=List[schemas.SpontaneousNote])
def get_notes_by_date(date_val: date, db: Session = Depends(get_db)):
    return crud.get_spontaneous_notes_by_date(db, target_date=date_val)

@router.post("/mark-displayed")
def mark_notes_displayed(note_ids: List[int], db: Session = Depends(get_db)):
    return {"success": crud.mark_notes_as_displayed(db, note_ids=note_ids)}
