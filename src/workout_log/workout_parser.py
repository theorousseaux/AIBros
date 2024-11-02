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
import base64

import httpx


class WorkoutLogger:
    def __init__(self):

        self.llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai_api_key)
        self.mllm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key)
        self.parser = JsonOutputParser(pydantic_object=Workout)
        self.system = """
        You are AI-BRO workout logger. 
        Take user's unstructured notes of the workout, and rewrite them in a structured way.
        Take care of counting the sets well. Usually, user will use separators like "-" or "/".
        If format is "12/12/12/12" or "4*12", it means 4 sets of 12 reps, so 4 new "Set" objects in the output.
        If an information is not mentioned, fill with None. 
        Follow this structure : {format_instructions}. \n
        """

    def setup_chain(self, mode):
        if mode == "mllm":
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system),
                    (
                        "human",
                        "Extract all the workout informations on the image and rewrite them.",
                    ),
                    (
                        "human",
                        [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/jpeg;base64,{input_img}"
                                },
                            }
                        ],
                    ),
                ]
            ).partial(format_instructions=self.parser.get_format_instructions())
            return self.prompt | self.mllm | self.parser
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system),
                ("human", "{input_text}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        return self.prompt | self.llm | self.parser

    def generate(self, input_text: str | None, input_img=None):

        if input_img is not None:
            img = base64.b64encode(input_img).decode("utf-8")
            chain = self.setup_chain(mode="mllm")
            return chain.invoke({"input_img": img})

        chain = self.setup_chain(mode="llm")
        return chain.invoke({"input_text": input_text})


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
    date: str = Field(
        description="The date of the workout in format '%d-%m-%Y %H:%M', if mentioned (otherwise : None) "
    )
    name: str = Field(description="Descriptive title for the workout")
    sets: List[Set] = Field(description="List of sets performed during the workout")


def workout_to_dataframe(workout: dict) -> pd.DataFrame:
    rows = []
    exercise_set_counter = defaultdict(int)

    for set_obj in workout["sets"]:
        exercise_name = set_obj["exercice"]["name"]
        exercise_set_counter[exercise_name] += 1
        if "date" in workout.keys():
            if workout["date"] is None or str(workout["date"]) == "None":
                date = datetime.now().strftime("%d-%m-%Y %H:%M")
            else:
                date = workout["date"]
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
