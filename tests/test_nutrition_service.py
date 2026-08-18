from datetime import date
import pytest
from backend.app.schemas import DailyNutritionCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.nutrition.service import NutritionService

class MockNutritionRepo:
    def __init__(self):
        self.logs = {}

    def get_by_date(self, log_date: date):
        return self.logs.get(log_date)

    def list_logs(self, start_date=None, end_date=None):
        return list(self.logs.values())

    def upsert(self, nutrition_in: DailyNutritionCreate):
        class DummyNut:
            def __init__(self, d, water, coffee):
                self.date = d
                self.water_cups = water
                self.coffee_cups = coffee

        nut_obj = DummyNut(nutrition_in.date, nutrition_in.water_cups, nutrition_in.coffee_cups)
        self.logs[nutrition_in.date] = nut_obj
        return nut_obj

    def delete(self, log_date: date):
        if log_date in self.logs:
            del self.logs[log_date]
            return True
        return False

def test_nutrition_service_crud():
    repo = MockNutritionRepo()
    service = NutritionService(repo)

    test_date = date(2026, 8, 18)
    nut_in = DailyNutritionCreate(date=test_date, water_cups=4.0, coffee_cups=2.0)

    saved = service.save_log(nut_in)
    assert saved.water_cups == 4.0
    assert saved.coffee_cups == 2.0

    retrieved = service.get_log(test_date)
    assert retrieved.water_cups == 4.0

    all_logs = service.list_logs()
    assert len(all_logs) == 1

    assert service.delete_log(test_date) is True
    with pytest.raises(EntityNotFoundException):
        service.get_log(test_date)
