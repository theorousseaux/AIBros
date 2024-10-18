import streamlit as st
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from src.nutritionist.agent import NutritionPipeline
from src.models import (
    State,
    DietPlanReport,
    CookBook,
    Meal,
    Ingredient,
    MacroNutritiens,
)
import pandas as pd

st.set_page_config(layout="wide")


def get_user_information(nickname: str) -> Dict:
    with open("data/users.json", "r") as f:
        all_info = json.load(f)
    for user in all_info["users"]:
        if user["nickname"].lower() == nickname.lower():
            return user
    return {}


def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def generate_response(workflow, input):
    output = workflow.invoke(input)
    display_diet_plan(diet_plan=output["diet_plan"])
    display_cookbook(cookbook=output["cookbook"])
    st.markdown(output["response"])


def display_cookbook(cookbook: CookBook):
    st.markdown("### Cookbook")
    for meal in cookbook["meals"]:
        with st.expander(meal["name"], expanded=False):
            st.dataframe(pd.DataFrame(data=meal["ingredients"]))
            st.markdown(f"Total : {meal['kcals']} kcal")
            st.markdown(meal["recipe"])
            st.json(meal["macros"])


def display_diet_plan(diet_plan=DietPlanReport):
    st.markdown("### Diet Plan")
    st.warning(f"{diet_plan['explanation']}")
    st.json(diet_plan["macros"])


def chat_interface(usernames):
    st.title("AI-Bro (Nutritionist)")

    username = st.sidebar.selectbox("Select user", usernames)
    user = get_user_information(username)
    with st.sidebar.expander("Personal information", expanded=True):
        st.dataframe(
            pd.DataFrame(data=user.values(), index=user.keys()),
            use_container_width=True,
        )

    nutri_bro = NutritionPipeline()
    nutri_pipe = nutri_bro.pipeline()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question := st.chat_input("What is up?"):
        initial_state = State(
            user_info=user,
            question=question,
            chat_history=st.session_state.chat_history,
            diet_plan=None,
            cookbook=None,
            response="",
        )
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            generate_response(workflow=nutri_pipe, input=initial_state)

            #     # diet_plan = s["nutritionist"]["diet_plan"]
            #     # report_col.warning(diet_plan["goal"])
            #     # report_col.dataframe(pd.DataFrame().from_dict(diet_plan["macros"]))
            # if "cook" in s.keys():
            #     cookbook = s["cook"]["cookbook"]
            #     chat_col.markdown("Let the cook cook...")
            #     for meal in cookbook["meals"]:
            #         chat_col.markdown(f"_{meal['content']}_ \n")
            #     report_col.warning(cookbook)
            # if "final_response" in s.keys():
            #     st.session_state.messages.append(
            #         {
            #             "role": "assistant",
            #             "content": s["final_response"]["response"],
            #         }
            #     )


def history_interface():
    st.title("Diet Plan and Cookbook History")

    if st.session_state.diet_plan_history:
        st.header("Diet Plan History")
        for i, plan in enumerate(st.session_state.diet_plan_history):
            with st.expander(f"Diet Plan {i+1}"):
                st.write(f"Goal: {plan.goal}")
                st.write(f"Daily Calorie Intake: {plan.kcal_intake} kcal")
                st.write(f"Method: {plan.method}")
                st.write("Macronutrients:")
                st.write(f"- Proteins: {plan.macros.proteins}g")
                st.write(f"- Fat: {plan.macros.fat}g")
                st.write(f"- Carbohydrates: {plan.macros.carbohydrates}g")
                st.write(f"Explanation: {plan.explanation}")

    if st.session_state.cookbook_history:
        st.header("Cookbook History")
        for i, cookbook in enumerate(st.session_state.cookbook_history):
            with st.expander(f"Cookbook {i+1}"):
                for j, meal in enumerate(cookbook.meals):
                    st.subheader(f"Meal {j+1}")
                    st.write(f"Content: {meal.content}")
                    st.write("Ingredients:")
                    for ingredient in meal.ingredients:
                        st.write(f"- {ingredient.name}: {ingredient.quantity}g")
                    st.write(f"Recipe: {meal.recipe}")
                    st.write(f"Total Calories: {meal.kcals} kcal")
                    st.write("Macronutrients:")
                    st.write(f"- Proteins: {meal.macros.proteins}g")
                    st.write(f"- Fat: {meal.macros.fat}g")
                    st.write(f"- Carbohydrates: {meal.macros.carbohydrates}g")


def main():
    initialize_session_state()

    st.sidebar.title("User settings")
    page = st.sidebar.radio("Mode", ["Nutritionist", "History"])

    if page == "Nutritionist":
        chat_interface(usernames=["dozo", "toubounou"])
    elif page == "History":
        history_interface()


if __name__ == "__main__":
    main()
