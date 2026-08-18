from datetime import date
import pytest
from backend.app.schemas import DailyLogCreate, SpontaneousNoteCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.daily_logs.service import DailyLogsService, NotesService

class MockDailyLogRepo:
    def __init__(self):
        self.logs = {}

    def get_by_date(self, log_date: date):
        return self.logs.get(log_date)

    def list_logs(self, start_date=None, end_date=None):
        return list(self.logs.values())

    def upsert(self, log_in: DailyLogCreate):
        class DummyLog:
            def __init__(self, d, mood_score):
                self.date = d
                self.mood_score = mood_score
                self.supplements = []

        log_obj = DummyLog(log_in.date, log_in.mood_score)
        self.logs[log_in.date] = log_obj
        return log_obj

    def delete(self, log_date: date):
        if log_date in self.logs:
            del self.logs[log_date]
            return True
        return False

def test_daily_logs_service_crud():
    repo = MockDailyLogRepo()
    service = DailyLogsService(repo)

    test_date = date(2026, 8, 18)
    log_in = DailyLogCreate(date=test_date, mood_score=8)
    
    # Save log
    saved = service.save_log(log_in)
    assert saved.mood_score == 8

    # Get log
    retrieved = service.get_log(test_date)
    assert retrieved.mood_score == 8

    # List logs
    all_logs = service.list_logs()
    assert len(all_logs) == 1

    # Delete log
    assert service.delete_log(test_date) is True
    with pytest.raises(EntityNotFoundException):
        service.get_log(test_date)
