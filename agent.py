import os
from dotenv import load_dotenv

load_dotenv()
import pandas as pd
import json
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field
from typing import Literal
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langgraph.graph.message import add_messages
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_experimental.utilities import PythonREPL
from langchain.memory import ConversationBufferMemory
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import HumanMessage
from typing import Dict, Any

openai_api_key = os.getenv("OPENAI_API_KEY")

from all_tools import BMRCalculatorTool, nutrition_db_retriever_tool


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str


class AIBRO:
    def __init__(self, llm="gpt-4o-mini", mllm="gpt-4o"):
        self.llm = ChatOpenAI(model=llm)
        self.mllm = ChatOpenAI(model=mllm)
        self.memory = ConversationBufferMemory(return_messages=True)

    def get_memory_as_string(self):
        """
        Retrieve the conversation history from memory as a string.
        """
        return "\n".join([msg.content for msg in self.memory.chat_memory.messages])

    def update_memory(self, role: str, message_content: str):
        """
        Update memory with the latest interaction.
        Role can be 'user' or the agent (e.g. 'nutritionist', 'bro', etc.)
        """
        self.memory.chat_memory.add_message(
            HumanMessage(content=message_content, name=role)
        )

    # def personal_info_writer(self, state):
    #     """
    #     Collects personal information from the user only if he give informations.
    #     """

    #     class PersonalInformation(BaseModel):
    #         name: str = Field(
    #             ..., description="The name of the user"
    #         )  # Mandatory field
    #         additional_info: Dict[str, Any] = Field(
    #             default_factory=dict,
    #             description="Any additional personal information as key-value pairs",
    #         )  # Arbitrary fields

    #     try:
    #         with open(f"personal_info/users.json", "r") as f:
    #             current_info = json.load(f)
    #     except Exception as e:
    #         current_info = e
    #     parser = JsonOutputParser(pydantic_object=PersonalInformation)
    #     prompt = ChatPromptTemplate.from_messages(
    #         [
    #             (
    #                 "system",
    #                 """You are the personal information writer for AI-Bro.\n
    #                 Take into account the current available information :{current_info}.\n
    #                 Store the information of the user in a structured way.\n{format_instructions}\n
    #                 """,
    #             ),
    #             MessagesPlaceholder(variable_name="messages"),
    #         ]
    #     ).partial(
    #         format_instructions=parser.get_format_instructions(),
    #         current_info=current_info,
    #     )
    #     chain = prompt | self.llm | parser
    #     result = chain.invoke(state)
    #     os.makedirs("personal_info", exist_ok=True)

    #     with open(f"personal_info/users.json", "a") as f:
    #         json.dump(result, f)

    #     return {"messages": [f"Collected Personal information : {result}"]}

    def route(self, state, members):

        system = f"""You are AIBro's decision maker, expert at managing a conversation between the following modes : {', '.join(members)}.
        Nutritionist mode is related to diet plan, nutrition advices, food and supplementation.\n
        Coach mode is related to sport and coaching, fitness advice, assistance, exercise analysis and workout planning.\n
        Bro mode is the general mode: chatting and motivational.\n
        Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. 
        If a mode needs further information from the user, ask bro mode to request info to the user.
        Only if the user provides personal informations, use the personal info writer to store them.
        """

        class routeResponse(BaseModel):
            next: Literal[*members] = Field(
                ...,
                description="Given the conversation above, what should be done next?"
                "Should we FINISH? Select one of: {members}",
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next?"
                    " Select one of:{members}.",
                ),
            ]
        ).partial(members=", ".join(members))

        router_chain = prompt | self.llm.with_structured_output(routeResponse)
        return router_chain.invoke(state)

    def nutritionist(self, state):
        tools = [
            DuckDuckGoSearchRun(),
            BMRCalculatorTool(),
            nutrition_db_retriever_tool,
        ]
        new_prompt = """
        AI-Bro changed to nutrition mode and is now expert in nutrition.\n
        He can:\n
        - make a diet plan by accessing relevant data on food and nutrients\n
        - calculate basal metabolic rate, total energy expenditure and calories intakes needed,
        based on the user's profile and objectives.\n
        If you don't have all the information you need, ask the user for further information.
        """
        agent = create_react_agent(self.llm, tools=tools, state_modifier=new_prompt)
        result = agent.invoke(state)
        return {
            "messages": [
                HumanMessage(
                    content=result["messages"][-1].content, name="nutritionist"
                )
            ]
        }

    def bro(self, state):
        conversation_history = self.get_memory_as_string()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""AI-Bro changed to bro mode and is now chatting with the user.\n
                    The conversation so far: {conversation_history}
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke(state)
        self.update_memory("bro", result.content)
        return {"messages": [result]}

    def create_graph(self, members):
        workflow = StateGraph(AgentState)
        workflow.add_node("router", lambda state: self.route(state, members=members))
        workflow.add_node("nutritionist", self.nutritionist)
        workflow.add_node("bro", self.bro)
        # workflow.add_node("personal_info_writer", self.personal_info_writer)

        workflow.add_edge(START, "router")

        workflow.add_edge("nutritionist", "router")
        # workflow.add_edge("personal_info_writer", "router")
        conditional_map = {k: k for k in members}
        workflow.add_conditional_edges("router", lambda x: x["next"], conditional_map)

        workflow.add_edge(START, "router")
        workflow.add_edge("bro", END)
        graph = workflow.compile()
        return graph
