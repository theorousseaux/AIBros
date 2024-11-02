import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import List
from pydantic import BaseModel, Field
from typing import Literal, Optional

import pandas as pd

from collections import defaultdict

openai_api_key = os.getenv("OPENAI_API_KEY")


class WorkoutLogger:
    def __init__(self, llm="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm, openai_api_key = openai_api_key)

        parser = JsonOutputParser(pydantic_object=Workout)
        system = """
        You are AI-BRO workout logger. 
        Take user's unstructured notes of the workout, and rewrite them in a structured way.
        Take care of counting the sets well. Usually, user will use separators like "-" or "/".
        If format is "12/12/12/12" or "4*12", it means 4 sets of 12 reps, so 4 new "Set" objects in the output.
        If an information is not mentioned, fill with None. 
        Follow this structure : {format_instructions}. \n
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{input}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        self.chain = prompt | self.llm | parser


class Exercice(BaseModel):
    name: str = Field(description="Name of the exercice")
    charge_type: Literal[
        "Poids du corps", "Haltère", "Barre", "Poulie", "Machine", "Smith Machine"
    ] = Field(description="Charge type used for mechanical resistance")
    # muscles: List[
    #     Literal[
    #         "Biceps",
    #         "Triceps",
    #         "Pectoraux",
    #         "Deltoide antérieur",
    #         "Deltoide latéral",
    #         "Deltoide postérieur",
    #         "Abdominaux",
    #         "Trapèzes",
    #         "Grand dorsal",
    #         "Quadriceps",
    #         "Ischios-jambiers",
    #         "Fessiers",
    #         "Mollets",
    #     ]
    # ] = Field(description="List of muscles involved in the exercice")


class Set(BaseModel):
    exercice: Exercice = Field(description="Exercice performed during the set")
    nb_reps: int = Field(description="Number of repetitions done during the set")
    charge: float = Field(description="Added weight used to perform the lift")
    rest: float = Field(description="Resting duration performed after the set")


class Workout(BaseModel):
    date: Optional[str] = Field(description="The date of the workout, if mentioned (otherwise : None) ")
    name: str = Field(description="Descriptive title for the workout")
    sets: List[Set] = Field(description="List of sets performed during the workout")


def workout_to_dataframe(workout: dict) -> pd.DataFrame:
    rows = []
    exercise_set_counter = defaultdict(int)

    for set_obj in workout["sets"]:
        exercise_name = set_obj["exercice"]["name"]
        exercise_set_counter[exercise_name] += 1
        if 'date' in set_obj.keys():
            if set_obj['date'] is None or str(set_obj['date']) == 'None':
                date = set_obj['date']
        else:
            date = datetime.now().strftime("%d-%m-%Y %H h")
        row = {
            "Date": date,
            "Workout name": workout["name"],
            "Set number ": exercise_set_counter[exercise_name],
            "Exercise name": exercise_name,
            "Equipment": set_obj["exercice"]["charge_type"],
            "Number of repetitions": set_obj["nb_reps"],
            "Charge (kg)": set_obj["charge"],
            "Rest time (sec)": set_obj["rest"],
        }
        rows.append(row)

    return pd.DataFrame(rows)


def add_workout_to_dataframe(workout: Workout, df: pd.DataFrame) -> pd.DataFrame:
    new_data = workout_to_dataframe(workout)
    return pd.concat([df, new_data], ignore_index=True)
