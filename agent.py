import os
from dotenv import load_dotenv

load_dotenv()

from langchain.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun


from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate


openai_api_key = os.getenv("OPENAI_API_KEY")

from all_tools import BMRCalculatorTool


class NutritionCoach:
    def __init__(self, model):
        self.llm = ChatOpenAI(model=model, openai_api_key=openai_api_key)
        self.tools = [DuckDuckGoSearchRun(), BMRCalculatorTool()]

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""You are AI-Bro, the perfect gym advisor, friend and coach.
                    You have multiple expertises : nutritionist, scientist, fitness coach, but you can also be a gymbro. \n
                    You have all these tools at your disposal: {self.tools}""",
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
            # output_parser=StrOutputParser(),
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=True
        )

    def stream(self, input):
        return self.agent_executor.stream(input)

    def invoke(self, input):
        return self.agent_executor.invoke(input)


if __name__ == "__main__":
    aibro = NutritionCoach(model="gpt-4o-mini")

    answer = aibro.invoke(
        input={
            "chat_history": [],
            "input": "hi bro i'm 24, 75kg and 180cm, what's my BMR ?",
        }
    )
    print(answer)
