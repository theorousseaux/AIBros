import os
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


from langchain_core.output_parsers import JsonOutputParser

from langchain.memory import ConversationBufferMemory
from langgraph.graph import END, StateGraph, START

openai_api_key = os.getenv("OPENAI_API_KEY")


from langchain.memory import ConversationBufferMemory
from models import *


class AIBRO:
    def __init__(self, llm="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm)
        self.chat_history = ConversationBufferMemory()

    def nutritionist(self, state: State):

        parser = JsonOutputParser(pydantic_object=DietPlanReport)
        system = """
        You are AI-BRO diet planner. To make a diet plan, follow these steps: \n
        1. Consider past info from the user :{user_info}\n
        2. Understand the user challenge : {question}\n
        3. Determine the strategy to take. What does he have to change in his diet?
        4. Then, proceed this way:
        4.1 Calculate total daily energy expenditure with the information you have\n
        4.2 Take a calorie deficit/surplus of 5-10 percent of total energy expenditure, depending on user's goal, \
        and determine the total kcal intake. \n
        4.3 Deduce macronutrients quantities per day. 1g of proteins or carbs is 4kcal and 1g of fat is 9 kcal, \
        the user needs 1g of fat/kg of bodyweight, 1 to 2g of proteins/kg of bodyweight (1 if sedentary, 2 if very sportive) and the rest in carbohydrates.\n
        4.4 Make your results in a structured output following : {format_instructions}. \n
        Context of conversation: {chat_history}\n
        Go on ! \n
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("placeholder", "{chat_history}"),
                ("human", "{question}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        chain = prompt | self.llm | parser
        diet_plan = chain.invoke(state)
        return {"diet_plan": diet_plan}

    def cook(self, state: State):

        parser = JsonOutputParser(pydantic_object=CookBook)
        system = """
        You are AI-BRO cook. To create meals , follow these steps: \n
        1. Consider diet plan :{diet_plan}\n
        2. Analyze user profile : {user_info}\n
        3. Build three meals : breakfast, lunch and diner to fit the diet plan and respect macronutrients and kcals.\n
        4. Put your meals in a cookbook using a structured output, following : {format_instructions}. \n
        Go on ! \n
        """
        prompt = ChatPromptTemplate.from_template(template=system).partial(
            format_instructions=parser.get_format_instructions()
        )

        chain = prompt | self.llm | parser
        cookbook = chain.invoke(state)
        return {"cookbook": cookbook}

    def generate_final_response(self, state: State):
        prompt = ChatPromptTemplate.from_template(
            """
        Based on the user's query: {question}
        And the generated diet plan: {diet_plan}
        And the cookbook: {cookbook}
        
        Please provide a comprehensive response to the user, including:
        1. A summary of the diet strategy
        2. Key points from the diet plan
        3. An overview of the meals in the cookbook
        4. Any additional advice or recommendations

        Make sure the response is well-structured, informative, and engaging.
        """
        )

        chain = prompt | self.llm
        # force output to State format?
        response = chain.invoke(state)
        return {"response": response.content}

    def define_graph(self):
        workflow = StateGraph(State)

        workflow.add_node("nutritionist", self.nutritionist)
        workflow.add_node("cook", self.cook)
        workflow.add_node("final_response", self.generate_final_response)

        workflow.add_edge("nutritionist", "cook")
        workflow.add_edge("cook", "final_response")
        workflow.add_edge("final_response", END)

        workflow.set_entry_point("nutritionist")

        return workflow.compile()
