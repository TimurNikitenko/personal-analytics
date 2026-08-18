"""
End-to-end API Contract Integration Test Suite.
Verifies all FastAPI endpoint contracts across domain layers.
"""

from datetime import date
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.routers.ml import get_ml_service

client = TestClient(app)

def test_daily_logs_api_contract():
    payload = {
        "date": "2026-08-18",
        "mood_score": 9,
        "energy": 8,
        "steps": 12000,
        "supplements": [
            {"name": "Vitamin D3", "dosage": 2000.0, "unit": "IU"}
        ]
    }
    response = client.post("/api/daily-logs/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-08-18"

    response = client.get("/api/daily-logs/2026-08-18")
    assert response.status_code == 200
    assert response.json()["mood_score"] == 9

    response = client.get("/api/daily-logs/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    response = client.delete("/api/daily-logs/2026-08-18")
    assert response.status_code == 200

def test_nutrition_api_contract():
    payload = {
        "date": "2026-08-18",
        "water_cups": 5.0,
        "coffee_cups": 2.0
    }
    response = client.post("/api/nutrition/", json=payload)
    assert response.status_code == 200

    response = client.get("/api/nutrition/2026-08-18")
    assert response.status_code == 200
    assert response.json()["water_cups"] == 5.0

    client.delete("/api/nutrition/2026-08-18")

def test_finances_api_contract():
    payload = {
        "date": "2026-08-18",
        "amount": 250.0,
        "category": "Software",
        "transaction_type": "expense"
    }
    response = client.post("/api/finances/", json=payload)
    assert response.status_code == 200
    fid = response.json()["id"]

    response = client.get("/api/finances/")
    assert response.status_code == 200

    response = client.delete(f"/api/finances/{fid}")
    assert response.status_code == 204

def test_learning_api_contract():
    payload = {
        "date": "2026-08-18",
        "topic": "Clean Architecture",
        "learning_hours": 2.0,
        "practice_hours": 3.0
    }
    response = client.post("/api/learning/", json=payload)
    assert response.status_code == 200
    lid = response.json()["id"]

    response = client.get("/api/learning/")
    assert response.status_code == 200

    client.delete(f"/api/learning/{lid}")

def test_medical_and_metrics_api_contract():
    m_payload = {"date": "2026-08-18", "metric_name": "Weight", "metric_value": "75.5", "unit": "kg"}
    response = client.post("/api/metrics/", json=m_payload)
    assert response.status_code == 200

    response = client.get("/api/metrics/names")
    assert response.status_code == 200

    t_payload = {"date": "2026-08-18", "test_name": "Vitamin D", "value": 45.0, "unit": "ng/mL"}
    response = client.post("/api/medical-tests/", json=t_payload)
    assert response.status_code == 200
    tid = response.json()["id"]

    client.delete(f"/api/medical-tests/{tid}")

def test_goals_api_contract():
    payload = {
        "area": "Engineering",
        "description": "Refactor codebase to Onion Architecture",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "status": "Active"
    }
    response = client.post("/api/goals/", json=payload)
    assert response.status_code == 200
    gid = response.json()["id"]

    response = client.get("/api/goals/")
    assert response.status_code == 200

    client.delete(f"/api/goals/{gid}")

def test_ml_dataset_api_contract():
    mock_ml_service = MagicMock()
    mock_ml_service.build_flattened_dataset.return_value = [{"date": "2026-08-18", "mood_score": 9}]
    app.dependency_overrides[get_ml_service] = lambda: mock_ml_service

    try:
        response = client.get("/api/ml/dataset")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_ml_service, None)
