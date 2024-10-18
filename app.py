import streamlit as st
from pathlib import Path
import os
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.agents_llm.nutritionist import NutritionPipeline
from backend.agents_llm.workout_parser import WorkoutLogger

from backend import workout_tracker
from backend.models import (
    State,
    DietPlanReport,
    CookBook,
    Meal,
    Ingredient,
    MacroNutritiens,
    Workout,
    Exercice,
    Set,
)
import pandas as pd
from datetime import datetime

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


def chat_interface(username):
    st.title("AI-Bro (Nutritionist)")
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


WORKOUT_LOGS = Path(os.path.join(os.getcwd(), "data", "workout_logs"))


def workout_log_interface(username):
    st.title(f"{username} workout log")
    user_workout_log = os.path.join(WORKOUT_LOGS, f"{username}.csv")
    if f"{username}.csv" not in os.listdir(WORKOUT_LOGS):
        st.error(f"No workout logged yet for {username}.")
        with st.spinner("Creating empty log..."):
            df = pd.DataFrame(
                columns=[
                    "workout_date",
                    "workout_name",
                    "set_id",
                    "exercise_name",
                    "charge_type",
                    "muscles",
                    "reps",
                    "charge",
                    "rest",
                ]
            )
            df.to_csv(user_workout_log)
    else:
        df = pd.read_csv(user_workout_log)

    if username not in st.session_state:
        st.session_state[username] = {}

    if "workout_df" not in st.session_state[username]:
        st.session_state[username]["workout_df"] = df

    uploaded_workout = st.text_area("Notes of the workout")
    col1, col2, col3 = st.columns(3)
    add_workout = col1.button("Log workout", use_container_width=True)
    save_workout = col2.button("Save", use_container_width=True)
    clear_workout = col3.button("Clear", use_container_width=True)
    if add_workout:
        workout_parser = WorkoutLogger()
        ph_output = st.empty()
        with st.spinner("BroCoach logging workout..."):
            workout = workout_parser.chain.invoke({"input": uploaded_workout})
            ph_output.write_stream(workout)
            st.session_state[username]["workout_df"] = (
                workout_tracker.add_workout_to_dataframe(
                    workout=workout, df=st.session_state[username]["workout_df"]
                )
            )
    if clear_workout:
        st.session_state[username]["workout_df"] = df
    st.dataframe(st.session_state[username]["workout_df"], use_container_width=True)

    if save_workout:
        st.session_state[username]["workout_df"].to_csv(user_workout_log)
        st.warning("Successfully saved workout")


def main():
    initialize_session_state()

    st.sidebar.title("User settings")
    page = st.sidebar.radio("Mode", ["Workout log", "Nutritionist"])
    username = st.sidebar.selectbox("Select user", ["dozo", "toubounou"])
    if page == "Nutritionist":
        chat_interface(username)
    elif page == "Workout log":
        workout_log_interface(username)


if __name__ == "__main__":
    main()
