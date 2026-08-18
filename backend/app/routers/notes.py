from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas
from backend.app.database import get_db
from backend.app.domains.daily_logs.repository import SQLAlchemySpontaneousNoteRepository
from backend.app.domains.daily_logs.service import NotesService

router = APIRouter(prefix="/notes", tags=["Spontaneous Notes"])

def get_notes_service(db: Session = Depends(get_db)) -> NotesService:
    repo = SQLAlchemySpontaneousNoteRepository(db)
    return NotesService(repo)

@router.post("/", response_model=schemas.SpontaneousNote)
@router.post("", response_model=schemas.SpontaneousNote)
def create_note(
    note_in: schemas.SpontaneousNoteCreate,
    service: NotesService = Depends(get_notes_service)
):
    return service.create_note(note_in)

@router.get("/undisplayed", response_model=List[schemas.SpontaneousNote])
def get_undisplayed_notes(service: NotesService = Depends(get_notes_service)):
    return service.get_undisplayed_notes()

@router.get("/by-date", response_model=List[schemas.SpontaneousNote])
def get_notes_by_date(date_val: date, service: NotesService = Depends(get_notes_service)):
    return service.get_notes_by_date(date_val)

@router.post("/mark-displayed")
def mark_notes_displayed(note_ids: List[int], service: NotesService = Depends(get_notes_service)):
    return {"success": service.mark_displayed(note_ids)}
