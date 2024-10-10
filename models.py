from typing import List
from pydantic import BaseModel, Field
from typing import Literal
from typing_extensions import TypedDict


class MacroNutritiens(BaseModel):
    proteins: float = Field(description="Quantity of proteins per day, in grams")
    fat: float = Field(description="Quantity of fat per day, in grams")
    carbohydrates: float = Field(
        description="Quantity of carbohydrates per day, in grams"
    )


class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient")
    quantity: float = Field(description="Quantity of the ingredient, in grams")


class Meal(BaseModel):
    content: str = Field(description="Content of the meal")
    ingredients: List[Ingredient] = Field(description="list of ingredients")
    recipe: str = Field(description="Recipe of the meal")
    kcals: float = Field(description="Total kcals of the meal")
    macros: MacroNutritiens = Field(description="Macronutrients of the meal")


class CookBook(BaseModel):
    meals: List[Meal] = Field(description="List of meals")


class DietPlanReport(BaseModel):
    goal: str = Field(description="goal to be reached")
    kcal_intake: float = Field(
        description="Total quantity of kcals to be eaten daily to reach goal"
    )
    method: str = Field(description="Method used to calculate kcal TDEE")
    macros: MacroNutritiens = Field(
        description="Quantity of macronutrients to be eaten daily"
    )
    explanation: str = Field(description="Short explanation on the strategy")


class State(TypedDict):
    user_info: str
    question: str
    chat_history: List[str]
    diet_plan: DietPlanReport
    cookbook: CookBook
    response: str
