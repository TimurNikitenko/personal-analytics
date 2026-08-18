from datetime import date
import pytest
from backend.app.schemas import StrengthWorkoutCreate, WorkoutSetCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.workouts.service import WorkoutsService

class MockWorkoutRepo:
    def __init__(self):
        self.workouts = {}

    def list_workouts(self, start_date=None, end_date=None):
        return list(self.workouts.values())

    def get_by_id(self, workout_id: int):
        return self.workouts.get(workout_id)

    def create_workout(self, workout_in: StrengthWorkoutCreate):
        class DummyWorkout:
            def __init__(self, wid, name, d):
                self.id = wid
                self.name = name
                self.date = d
                self.sets = []

        wid = len(self.workouts) + 1
        w_obj = DummyWorkout(wid, workout_in.name, workout_in.date)
        self.workouts[wid] = w_obj
        return w_obj

    def delete_workout(self, workout_id: int):
        if workout_id in self.workouts:
            del self.workouts[workout_id]
            return True
        return False

def test_workouts_service_crud_and_1rm():
    repo = MockWorkoutRepo()
    service = WorkoutsService(repo)

    # Test 1RM Epley calculation
    assert service.calculate_one_rep_max(100.0, 1) == 100.0
    assert service.calculate_one_rep_max(100.0, 10) == 133.33

    # Test Create Workout
    w_in = StrengthWorkoutCreate(name="Chest & Triceps", date=date(2026, 8, 18), duration_seconds=3600, sets=[])
    created = service.create_workout(w_in)
    assert created.name == "Chest & Triceps"
    assert created.id == 1

    # Test Get Workout
    retrieved = service.get_workout(1)
    assert retrieved.name == "Chest & Triceps"

    # Test Delete Workout
    assert service.delete_workout(1) is True
    with pytest.raises(EntityNotFoundException):
        service.get_workout(1)
