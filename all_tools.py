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


class ProfileInput(BaseModel):
    height: int = Field(description="height of the user, in cm")
    weight: int = Field(description="weight of the user, in kg")
    gender: str = Field(description="gender of the user, either 'male' or 'female'")
    age: int = Field(description="Age of the user in years")


# class NutritionDatabaseTool(BaseTool):
#     name: str = "nutrition_database"
#     description: str = (
#         "Use this tool to query the nutrition database for information about foods and their nutritional content."
#     )
#     agent: Any = Field(
#         ..., description="The pandas agent used for querying the nutrition database"
#     )

#     def __init__(self, agent):
#         super().__init__()
#         self.agent = agent

#     def _run(self, query: str) -> str:
#         return self.agent.run(query)

#     async def _arun(self, query: str) -> str:
#         # For simplicity, we're using the synchronous version
#         return self._run(query)


class BMRCalculatorTool(BaseTool):
    name: str = "BMRCalculator"
    description: str = (
        "Mifflin St Jeor formula for calculating resting energy expenditure (or basal metabolic rate)"
    )
    args_schema: Type[BaseModel] = ProfileInput
    return_direct: bool = True

    def _run(
        self,
        height: int,
        weight: int,
        gender: str,
        age: int,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""

        if gender == "male":
            return 10 * weight + 6.25 * height - 5 * age + 5
        elif gender == "female":
            return 10 * weight + 6.25 * height - 5 * age - 161


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
