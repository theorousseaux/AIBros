from typing import List
from pydantic import BaseModel, Field
from typing import Literal
from typing_extensions import TypedDict
from datetime import datetime


class MacroNutritiens(BaseModel):
    g_proteins: float = Field(description="Grams of proteins")
    g_fat: float = Field(description="Grams of fat")
    g_carbohydrates: float = Field(description="Grams of carbohydrates")


class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient")
    quantity: str = Field(
        description="Quantity of the ingredient, with unity of measurement of the quantity (g or mL)"
    )


class Meal(BaseModel):
    name: str = Field(description="name of the meal")
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
    cookbook: List[Meal]
    response: str


class Exercice(BaseModel):
    name: str = Field(description="Name of the exercice")
    charge_type: Literal[
        "Poids du corps", "Haltère", "Barre", "Poulie", "Machine", "Smith Machine"
    ] = Field(description="Charge type used for mechanical resistance")
    muscles: List[
        Literal[
            "Biceps",
            "Triceps",
            "Pectoraux",
            "Deltoide antérieur",
            "Deltoide latéral",
            "Deltoide postérieur",
            "Abdominaux",
            "Trapèzes",
            "Grand dorsal",
            "Quadriceps",
            "Ischios-jambiers",
            "Fessiers",
            "Mollets",
        ]
    ] = Field(description="List of muscles involved in the exercice")


class Set(BaseModel):
    exercice: Exercice = Field(description="Exercice performed during the set")
    nb_reps: int = Field(description="Number of repetitions done during the set")
    charge: float = Field(description="Added weight used to perform the lift")
    rest: float = Field(description="Resting duration performed after the set")


class Workout(BaseModel):
    name: str = Field(description="Descriptive title for the workout")
    sets: List[Set] = Field(description="List of sets performed during the workout")