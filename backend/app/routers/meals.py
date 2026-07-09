from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from backend.app import schemas, crud
from backend.app.database import get_db

router = APIRouter(prefix="/meals", tags=["Meals"])

@router.get("/food-products", response_model=List[schemas.FoodProduct])
def read_food_products(db: Session = Depends(get_db)):
    return crud.get_food_products(db)

@router.post("/food-products", response_model=schemas.FoodProduct)
def add_food_product(product_in: schemas.FoodProductCreate, db: Session = Depends(get_db)):
    return crud.create_food_product(db, product_in=product_in)

@router.get("/", response_model=List[schemas.Meal])
@router.get("", response_model=List[schemas.Meal])
def read_meals_by_date(date_val: date, db: Session = Depends(get_db)):
    return crud.get_meals_by_date(db, target_date=date_val)

@router.post("/", response_model=schemas.Meal)
@router.post("", response_model=schemas.Meal)
def create_meal_log(meal_in: schemas.MealCreate, db: Session = Depends(get_db)):
    return crud.upsert_meal(db, meal_in=meal_in)
