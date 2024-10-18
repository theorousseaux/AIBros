import os
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


from langchain_core.output_parsers import JsonOutputParser

openai_api_key = os.getenv("OPENAI_API_KEY")

from ..models import *


class WorkoutLogger:
    def __init__(self, llm="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm)

        parser = JsonOutputParser(pydantic_object=Workout)
        system = """
        You are AI-BRO workout logger. 
        Take user's unstructured notes of the workout, and rewrite them in a structured way.
        Take care of counting the sets well. Usually, user will use separators like "-" or "/".
        If format is "12/12/12/12" or "4*12", it means 4 sets of 12 reps.
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
