"""
SQLAlchemy repository implementations for Nutrition and Meals.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.domains.nutrition.interfaces import INutritionRepository, IMealRepository

class SQLAlchemyNutritionRepository(INutritionRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_date(self, log_date: date) -> Optional[models.DailyNutrition]:
        return self.db.query(models.DailyNutrition).filter(models.DailyNutrition.date == log_date).first()

    def list_logs(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DailyNutrition]:
        query = self.db.query(models.DailyNutrition)
        if start_date:
            query = query.filter(models.DailyNutrition.date >= start_date)
        if end_date:
            query = query.filter(models.DailyNutrition.date <= end_date)
        return query.order_by(models.DailyNutrition.date.desc()).all()

    def upsert(self, nutrition_in: schemas.DailyNutritionCreate) -> models.DailyNutrition:
        db_nut = self.get_by_date(nutrition_in.date)
        if db_nut:
            nut_data = nutrition_in.model_dump(exclude_unset=True)
            for key, value in nut_data.items():
                setattr(db_nut, key, value)
        else:
            db_nut = models.DailyNutrition(**nutrition_in.model_dump())
            self.db.add(db_nut)
        self.db.commit()
        self.db.refresh(db_nut)
        return db_nut

    def delete(self, log_date: date) -> bool:
        db_nut = self.get_by_date(log_date)
        if db_nut:
            self.db.delete(db_nut)
            self.db.commit()
            return True
        return False

class SQLAlchemyMealRepository(IMealRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_food_products(self) -> List[models.FoodProduct]:
        return self.db.query(models.FoodProduct).order_by(models.FoodProduct.name.asc()).all()

    def create_food_product(self, product_in: schemas.FoodProductCreate) -> models.FoodProduct:
        existing = self.db.query(models.FoodProduct).filter(models.FoodProduct.name == product_in.name).first()
        if existing:
            return existing
        db_product = models.FoodProduct(**product_in.model_dump())
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def get_by_date(self, target_date: date) -> List[models.Meal]:
        return self.db.query(models.Meal).filter(models.Meal.date == target_date).order_by(models.Meal.meal_type.asc()).all()

    def upsert_meal(self, meal_in: schemas.MealCreate) -> models.Meal:
        db_meal = self.db.query(models.Meal).filter(
            models.Meal.date == meal_in.date,
            models.Meal.meal_type == meal_in.meal_type
        ).first()

        if db_meal:
            if meal_in.photo_path is not None:
                db_meal.photo_path = meal_in.photo_path
            self.db.commit()
            self.db.refresh(db_meal)
        else:
            db_meal = models.Meal(
                date=meal_in.date,
                meal_type=meal_in.meal_type,
                photo_path=meal_in.photo_path
            )
            self.db.add(db_meal)
            self.db.commit()
            self.db.refresh(db_meal)

        self.db.query(models.MealItem).filter(models.MealItem.meal_id == db_meal.id).delete()
        for item_in in meal_in.items:
            db_item = models.MealItem(
                meal_id=db_meal.id,
                product_name=item_in.product_name,
                quantity=item_in.quantity,
                unit=item_in.unit
            )
            self.db.add(db_item)
            self.create_food_product(schemas.FoodProductCreate(name=item_in.product_name, default_unit=item_in.unit))

        self.db.commit()
        self.db.refresh(db_meal)
        return db_meal
