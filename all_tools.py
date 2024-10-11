import os
import json
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from pydantic import BaseModel, Field
from typing import Any
from langchain_community.document_loaders.excel import UnstructuredExcelLoader


def get_user_information(nickname: str):
    with open("personal_info/users.json", "r") as f:
        all_info = json.load(f)
    for user in all_info["users"]:
        if user["nickname"].lower() == nickname.lower():
            return user
    return {}


class PersonalInformation(BaseModel):
    name: str = Field(
        description="The name of the user",
    )  # Mandatory field
    gender: str = Field(
        description="The gender of the user, either 'M' or 'F'",
    )
    age: int = Field(description="The age of the user, in years")
    weight: float = Field(description="The weight of the user, in kg")
    height: float = Field(description="The height of the user, in cm")
    activity_factor: float = Field(
        description="""
The activity factor of the user, according to user's information : 
Bed rest : 1.0-1.1, 
Sedentary :1.2 , 
Light exercise (1-3 days per week) : 1.3, 
Moderate exercise (3-5 days per week) : 1.5,
Heavy exercise (6-7 days per week) : 1.7,
Very heavy exercise (twice per day, extra heavy workouts) : 1.9
""",
    )


class PersonalInformationWriterTool(BaseTool):
    name: str = "personal_information_writer"
    description: str = "Writes the personal information of the user in a json file"
    args_schema: Type[BaseModel] = PersonalInformation
    return_direct: bool = True

    def _run(
        self,
        personal_info: PersonalInformation,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        print(personal_info)
        os.makedirs("personal_info", exist_ok=True)
        existing_users = os.listdir("personal_info")
        if "name" in personal_info.keys():
            username = personal_info["name"]
        else:
            username = "user"
        if f"{username}.json" in existing_users:
            with open(f"personal_info/{username}.json", "r") as f:
                existing_info = json.load(f)
        else:
            existing_info = {}
        new_info = personal_info.model_dump()
        user_info = dict(existing_info.items() & new_info.items())
        with open(f"personal_info/{username}.json", "w") as f:
            json.dump(user_info, f)

        return user_info


class PersonalInformationRetrieverTool(BaseTool):
    name: str = "personal_information_retriever"
    description: str = (
        "Search the personal information of the user in the list of clients"
    )
    return_direct: bool = True

    def _run(
        self,
        task: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""

        with open(f"personal_info/users.json", "r") as f:
            existing_info = json.load(f)

        return existing_info


class CalorieIntakeCalculatorTool(BaseTool):
    name: str = "kcal_intake_calculator"
    description: str = (
        "Calorie intake calculator, based on activity factor and Mifflin St Jeor formula for resting energy expenditure (or basal metabolic rate)"
    )
    args_schema: Type[BaseModel] = PersonalInformation
    return_direct: bool = True

    def _run(
        self,
        personal_info: PersonalInformation,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""

        if personal_info.gender == "male":
            return (
                10 * personal_info.weight
                + 6.25 * personal_info.height
                - 5 * personal_info.age
                + 5
            ) * personal_info.activity_factor
        elif personal_info.gender == "female":
            return (
                10 * personal_info.weight
                + 6.25 * personal_info.height
                - 5 * personal_info.age
                - 161
            ) * personal_info.activity_factor


def nutrition_db_retriever_tool():
    """
    Retrieves relevant information about nutrition.
    """
    loader = UnstructuredExcelLoader(
        "datasets/apports_nutritionnels.xlsx", mode="elements"
    )
    urls = [
        "https://ai.hubermanlab.com/s/idROLBEo",
        "https://www.hubermanlab.com/newsletter/foundational-fitness-protocol",
        "https://www.hubermanlab.com/newsletter/improve-your-sleep",
    ]
    docs = [WebBaseLoader(url).load() for url in urls] + loader.load()
    docs_list = [item for sublist in docs for item in sublist]

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)

    # Add to vectorDB
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever()

    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_blog_posts",
        "Search and return information about Huberman advices on fitness, nutrition, sleep and health.",
    )

    return retriever_tool
