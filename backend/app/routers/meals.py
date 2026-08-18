from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from backend.app import schemas
from backend.app.database import get_db
from backend.app.domains.nutrition.repository import SQLAlchemyMealRepository
from backend.app.domains.nutrition.service import MealService

router = APIRouter(prefix="/meals", tags=["Meals"])

def get_meal_service(db: Session = Depends(get_db)) -> MealService:
    repo = SQLAlchemyMealRepository(db)
    return MealService(repo)

@router.get("/food-products", response_model=List[schemas.FoodProduct])
def read_food_products(service: MealService = Depends(get_meal_service)):
    return service.get_food_products()

@router.post("/food-products", response_model=schemas.FoodProduct)
def add_food_product(
    product_in: schemas.FoodProductCreate,
    service: MealService = Depends(get_meal_service)
):
    return service.create_food_product(product_in)

@router.get("/", response_model=List[schemas.Meal])
@router.get("", response_model=List[schemas.Meal])
def read_meals_by_date(date_val: date, service: MealService = Depends(get_meal_service)):
    return service.get_meals_by_date(date_val)

@router.post("/", response_model=schemas.Meal)
@router.post("", response_model=schemas.Meal)
def create_meal_log(
    meal_in: schemas.MealCreate,
    service: MealService = Depends(get_meal_service)
):
    return service.upsert_meal(meal_in)
