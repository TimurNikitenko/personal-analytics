import os
import httpx
from datetime import date, datetime
from typing import List, Dict, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class APIClient:
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = httpx.get(f"{self.base_url}{endpoint}", params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP GET Error on {endpoint}: {e}")
            raise

    def _post(self, endpoint: str, json_data: Any) -> Any:
        try:
            response = httpx.post(f"{self.base_url}{endpoint}", json=json_data, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP POST Error on {endpoint}: {e}")
            raise

    def _put(self, endpoint: str, json_data: Any) -> Any:
        try:
            response = httpx.put(f"{self.base_url}{endpoint}", json=json_data, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP PUT Error on {endpoint}: {e}")
            raise

    def _delete(self, endpoint: str) -> None:
        try:
            response = httpx.delete(f"{self.base_url}{endpoint}", timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"HTTP DELETE Error on {endpoint}: {e}")
            raise

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

    # === Machine Learning ===
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

    # === Nutrition ===
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

    # === Experiment Days ===
    def get_experiment_days(self, experiment_id: int) -> List[Dict[str, Any]]:
        return self._get(f"/api/experiments/{experiment_id}/days")

    def upsert_experiment_day(self, experiment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post(f"/api/experiments/{experiment_id}/days", json_data=data)

    def delete_experiment_day(self, experiment_id: int, date_str: str) -> None:
        self._delete(f"/api/experiments/{experiment_id}/days/{date_str}")

    # === Statistical Analysis ===
    def analyze_experiment(self, experiment_id: int) -> Dict[str, Any]:
        return self._get(f"/api/experiments/{experiment_id}/analyze")

    def get_metric_baseline_stats(self, metric_source: str, metric_name: str) -> Dict[str, Any]:
        params = {"metric_source": metric_source, "metric_name": metric_name}
        return self._get("/api/experiments/helpers/baseline-stats", params=params)

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

    def import_strength_workouts_csv(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        try:
            response = httpx.post(f"{self.base_url}/api/strength-workouts/import", files=files, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP POST CSV Import Error: {e}")
            raise

    # === Meals ===
    def get_meals_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        return self._get("/api/meals/", params={"date_val": target_date.isoformat()})

    # === Notes ===
    def get_notes_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        return self._get("/api/notes/by-date", params={"date_val": target_date.isoformat()})

api_client = APIClient()


