from datetime import date
import pytest
from backend.app.schemas import GoalCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.goals.service import GoalsService

class MockGoalRepo:
    def __init__(self):
        self.goals = {}

    def list_goals(self, status=None):
        return list(self.goals.values())

    def get_by_id(self, goal_id: int):
        return self.goals.get(goal_id)

    def create_goal(self, goal_in: GoalCreate):
        class DummyGoal:
            def __init__(self, gid, area, desc, status):
                self.id = gid
                self.area = area
                self.description = desc
                self.status = status

        gid = len(self.goals) + 1
        obj = DummyGoal(gid, goal_in.area, goal_in.description, goal_in.status)
        self.goals[gid] = obj
        return obj

    def update_goal(self, goal_id: int, goal_in: GoalCreate):
        if goal_id in self.goals:
            self.goals[goal_id].description = goal_in.description
            self.goals[goal_id].status = goal_in.status
            return self.goals[goal_id]
        return None

    def delete_goal(self, goal_id: int):
        if goal_id in self.goals:
            del self.goals[goal_id]
            return True
        return False

def test_goals_service_crud():
    repo = MockGoalRepo()
    service = GoalsService(repo)

    g_in = GoalCreate(
        area="Health",
        description="Run 42km",
        target_metric="Distance",
        target_value=42.2,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="Active"
    )
    created = service.create_goal(g_in)
    assert created.description == "Run 42km"
    assert created.id == 1

    g_update = GoalCreate(
        area="Health",
        description="Run 50km",
        target_metric="Distance",
        target_value=50.0,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="Active"
    )
    updated = service.update_goal(1, g_update)
    assert updated.description == "Run 50km"

    assert service.delete_goal(1) is True
    with pytest.raises(EntityNotFoundException):
        service.delete_goal(1)
