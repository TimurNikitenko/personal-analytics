"""
Domain interfaces and repository protocols for Nutrition and Meals.
"""

from typing import Protocol, List, Optional
from datetime import date
from backend.app import models, schemas

class INutritionRepository(Protocol):
    def get_by_date(self, log_date: date) -> Optional[models.DailyNutrition]:
        ...

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyNutrition]:
        ...

    def upsert(self, nutrition_in: schemas.DailyNutritionCreate) -> models.DailyNutrition:
        ...

    def delete(self, log_date: date) -> bool:
        ...

class IMealRepository(Protocol):
    def get_food_products(self) -> List[models.FoodProduct]:
        ...

    def create_food_product(self, product_in: schemas.FoodProductCreate) -> models.FoodProduct:
        ...

    def get_by_date(self, target_date: date) -> List[models.Meal]:
        ...

    def upsert_meal(self, meal_in: schemas.MealCreate) -> models.Meal:
        ...
