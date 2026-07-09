import os
import sys
# Set database URL to sqlite before importing backend modules to avoid PostgreSQL dependency
os.environ["DATABASE_URL"] = "sqlite:///./test_meals_notes.db"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.database import Base, get_db

# Use an in-memory SQLite database for testing backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_meals_notes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clear tables before each test
    db = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

def test_create_and_get_food_product():
    # Test POST
    payload = {"name": "Яблоко", "default_unit": "штука"}
    response = client.post("/api/meals/food-products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Яблоко"
    assert data["default_unit"] == "штука"
    assert "id" in data

    # Test GET
    response = client.get("/api/meals/food-products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Яблоко"

def test_create_and_get_meal():
    # Pre-add a food product to test relation
    client.post("/api/meals/food-products", json={"name": "Овсяные хлопья", "default_unit": "грамм"})
    
    # Test POST meal
    meal_payload = {
        "date": "2026-07-09",
        "meal_type": "Breakfast",
        "items": [
            {"product_name": "Овсяные хлопья", "quantity": 150.0, "unit": "грамм"},
            {"product_name": "Новый Продукт", "quantity": 1.0, "unit": "штука"} # Should auto-create
        ],
        "photo_path": "/uploads/images/meal_breakfast.jpg"
    }
    
    response = client.post("/api/meals/", json=meal_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["meal_type"] == "Breakfast"
    assert data["photo_path"] == "/uploads/images/meal_breakfast.jpg"
    assert len(data["items"]) == 2
    
    # Verify auto-creation of food product
    response = client.get("/api/meals/food-products")
    products = [p["name"] for p in response.json()]
    assert "Новый Продукт" in products

    # Test GET meals
    response = client.get("/api/meals/?date_val=2026-07-09")
    assert response.status_code == 200
    meals = response.json()
    assert len(meals) == 1
    assert meals[0]["meal_type"] == "Breakfast"

def test_spontaneous_notes():
    # Test POST note
    note_payload = {
        "note_text": "Купить хлеб",
        "file_path": None,
        "file_type": "text"
    }
    response = client.post("/api/notes/", json=note_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["note_text"] == "Купить хлеб"
    assert data["displayed"] is False

    # Test GET undisplayed
    response = client.get("/api/notes/undisplayed")
    assert response.status_code == 200
    undisplayed = response.json()
    assert len(undisplayed) == 1
    assert undisplayed[0]["note_text"] == "Купить хлеб"
    note_id = undisplayed[0]["id"]

    # Test mark-displayed
    response = client.post("/api/notes/mark-displayed", json=[note_id])
    assert response.status_code == 200
    
    # Verify now it is empty
    response = client.get("/api/notes/undisplayed")
    assert len(response.json()) == 0

# Clean up SQLite file after tests run
@pytest.fixture(scope="session", autouse=True)
def cleanup_sqlite_file():
    yield
    if os.path.exists("./test_meals_notes.db"):
        os.remove("./test_meals_notes.db")
