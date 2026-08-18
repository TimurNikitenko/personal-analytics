"""
Domain Application Services for Nutrition and Meals.
"""

from typing import List, Optional
from datetime import date
from backend.app import models, schemas
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.nutrition.interfaces import INutritionRepository, IMealRepository

class NutritionService:
    def __init__(self, repo: INutritionRepository):
        self.repo = repo

    def get_log(self, log_date: date) -> models.DailyNutrition:
        db_nut = self.repo.get_by_date(log_date)
        if not db_nut:
            raise EntityNotFoundException(entity_name="DailyNutrition", identifier=str(log_date))
        return db_nut

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyNutrition]:
        return self.repo.list_logs(start_date=start_date, end_date=end_date)

    def save_log(self, nutrition_in: schemas.DailyNutritionCreate) -> models.DailyNutrition:
        return self.repo.upsert(nutrition_in)

    def delete_log(self, log_date: date) -> bool:
        success = self.repo.delete(log_date)
        if not success:
            raise EntityNotFoundException(entity_name="DailyNutrition", identifier=str(log_date))
        return True

class MealService:
    def __init__(self, repo: IMealRepository):
        self.repo = repo

    def get_food_products(self) -> List[models.FoodProduct]:
        return self.repo.get_food_products()

    def create_food_product(self, product_in: schemas.FoodProductCreate) -> models.FoodProduct:
        return self.repo.create_food_product(product_in)

    def get_meals_by_date(self, target_date: date) -> List[models.Meal]:
        return self.repo.get_by_date(target_date)

    def upsert_meal(self, meal_in: schemas.MealCreate) -> models.Meal:
        return self.repo.upsert_meal(meal_in)
