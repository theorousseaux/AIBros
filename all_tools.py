from langchain.tools import tool, BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Literal
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)


class ProfileInput(BaseModel):
    height: int = Field(description="height of the user, in cm")
    weight: int = Field(description="weight of the user, in kg")
    gender: str = Field(description="gender of the user, either 'male' or 'female'")
    age: int = Field(description="Age of the user in years")


class BMRCalculatorTool(BaseTool):
    name: str = "BMRCalculator"
    description: str = "useful for when you need to answer questions about math"
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
