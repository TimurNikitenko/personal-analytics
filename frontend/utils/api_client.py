"""
Unified APIClient for Frontend.
Inherits from BaseHTTPClient and delegates to modular domain endpoints.
"""

import os
from datetime import date
from typing import List, Dict, Any, Optional
import httpx
from frontend.utils.clients.base import BaseHTTPClient, BACKEND_URL

class APIClient(BaseHTTPClient):
    # === Daily Logs ===
    def get_daily_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/daily-logs/", params=params)

    def get_daily_log(self, log_date: date) -> Dict[str, Any]:
        return self._get(f"/api/daily-logs/{log_date.isoformat()}")

    def upsert_daily_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/daily-logs/", json_data=data)

    def delete_daily_log(self, log_date: date) -> None:
        self._delete(f"/api/daily-logs/{log_date.isoformat()}")

    # === Finances ===
    def get_finances(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/finances/", params=params)

    def create_finance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/finances/", json_data=data)

    def create_bulk_finances(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._post("/api/finances/bulk", json_data=data)

    def delete_finance(self, finance_id: int) -> None:
        self._delete(f"/api/finances/{finance_id}")

    # === Metrics ===
    def get_metrics(self, metric_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if metric_name:
            params["metric_name"] = metric_name
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/metrics/", params=params)

    def get_metric_names(self) -> List[str]:
        return self._get("/api/metrics/names")

    def create_metric(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/metrics/", json_data=data)

    # === Learning ===
    def get_learning_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/learning/", params=params)

    def create_learning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/learning/", json_data=data)

    def delete_learning(self, learning_id: int) -> None:
        self._delete(f"/api/learning/{learning_id}")

    # === Goals ===
    def get_goals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if status:
            params["status"] = status
        return self._get("/api/goals/", params=params)

    def create_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/goals/", json_data=data)

    def update_goal(self, goal_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._put(f"/api/goals/{goal_id}", json_data=data)

    def delete_goal(self, goal_id: int) -> None:
        self._delete(f"/api/goals/{goal_id}")

    # === Export ===
    def get_export_url(self) -> str:
        return f"{self.base_url}/api/export"

    # === ML Dataset ===
    def get_ml_dataset(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/ml/dataset", params=params)

    # === Telegram Bot ===
    def send_telegram_test_reminder(self) -> Dict[str, Any]:
        return self._post("/api/telegram/test-reminder", json_data={})

    # === Nutrition & Meals ===
    def get_nutrition_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/nutrition/", params=params)

    def get_nutrition_log(self, log_date: date) -> Optional[Dict[str, Any]]:
        try:
            return self._get(f"/api/nutrition/{log_date.isoformat()}")
        except Exception:
            return None

    def upsert_nutrition_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/nutrition/", json_data=data)

    def delete_nutrition_log(self, log_date: date) -> None:
        self._delete(f"/api/nutrition/{log_date.isoformat()}")

    # === Medical Tests ===
    def get_medical_tests(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        test_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if test_name:
            params["test_name"] = test_name
        return self._get("/api/medical-tests/", params=params)

    def create_medical_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/medical-tests/", json_data=data)

    def delete_medical_test(self, test_id: int) -> None:
        self._delete(f"/api/medical-tests/{test_id}")

    # === Experiments ===
    def get_experiments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if status:
            params["status"] = status
        return self._get("/api/experiments/", params=params)

    def get_experiment(self, experiment_id: int) -> Dict[str, Any]:
        return self._get(f"/api/experiments/{experiment_id}")

    def create_experiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/experiments/", json_data=data)

    def update_experiment(self, experiment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._put(f"/api/experiments/{experiment_id}", json_data=data)

    def delete_experiment(self, experiment_id: int) -> None:
        self._delete(f"/api/experiments/{experiment_id}")

    def get_experiment_days(self, experiment_id: int) -> List[Dict[str, Any]]:
        return self._get(f"/api/experiments/{experiment_id}/days")

    def upsert_experiment_day(self, experiment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post(f"/api/experiments/{experiment_id}/days", json_data=data)

    def log_experiment_day(self, experiment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.upsert_experiment_day(experiment_id, data)

    def delete_experiment_day(self, experiment_id: int, date_val_or_str: Any) -> None:
        date_str = date_val_or_str.isoformat() if hasattr(date_val_or_str, 'isoformat') else str(date_val_or_str)
        self._delete(f"/api/experiments/{experiment_id}/days/{date_str}")

    def analyze_experiment(self, experiment_id: int) -> Dict[str, Any]:
        return self._get(f"/api/experiments/{experiment_id}/analyze")

    def get_baseline_stats(self, metric_source: str, metric_name: str) -> Dict[str, Any]:
        params = {"metric_source": metric_source, "metric_name": metric_name}
        return self._get("/api/experiments/helpers/baseline-stats", params=params)

    def get_metric_baseline_stats(self, metric_source: str, metric_name: str) -> Dict[str, Any]:
        return self.get_baseline_stats(metric_source, metric_name)

    # === Strength Workouts ===
    def get_strength_workouts(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/strength-workouts/", params=params)

    def create_strength_workout(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/strength-workouts/", json_data=data)

    def delete_strength_workout(self, workout_id: int) -> None:
        self._delete(f"/api/strength-workouts/{workout_id}")

    def import_workouts_csv(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        return self._post("/api/strength-workouts/import", files=files)

    def import_strength_workouts_csv(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        return self.import_workouts_csv(file_bytes, filename)

    # === Spontaneous Notes ===
    def create_spontaneous_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/notes/", json_data=data)

    def get_undisplayed_notes(self) -> List[Dict[str, Any]]:
        return self._get("/api/notes/undisplayed")

    def get_notes_by_date(self, date_val: date) -> List[Dict[str, Any]]:
        params = {"date_val": date_val.isoformat()}
        return self._get("/api/notes/by-date", params=params)

    def mark_notes_displayed(self, note_ids: List[int]) -> Dict[str, Any]:
        return self._post("/api/notes/mark-displayed", json_data=note_ids)

    # === Meals & Food Products ===
    def get_food_products(self) -> List[Dict[str, Any]]:
        return self._get("/api/meals/food-products")

    def create_food_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/meals/food-products", json_data=data)

    def get_meals_by_date(self, date_val: date) -> List[Dict[str, Any]]:
        params = {"date_val": date_val.isoformat()}
        return self._get("/api/meals/", params=params)

    def create_meal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/meals/", json_data=data)

    # === Agent Insights ===
    def get_agent_insights(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._get("/api/agent-insights/", params=params)

    def create_agent_insight(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/agent-insights/", json_data=data)

    def delete_agent_insight(self, insight_id: int) -> None:
        self._delete(f"/api/agent-insights/{insight_id}")

api_client = APIClient()
