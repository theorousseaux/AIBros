import streamlit as st
from pathlib import Path
import os
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.agents_llm.nutritionist import NutritionPipeline
from src.workout_log.workout_parser import *
from backend.models import *
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")


def workout_log_interface(username):
    st.title(f"Logger")
    upload_workout = st.expander(
        "Upload an existing workout (text or image)", expanded=True
    )

    start_workout = st.expander("Start a fresh new workout")
    with upload_workout:
        upload_mode = st.radio("Format", ["Photo", "Text"])
        if upload_mode == "Photo":
            uploaded_image = st.file_uploader("Photograph of your workout notes")
        elif upload_mode == "Text":
            uploaded_text = st.text_area("Notes of your workout")
            if st.button("Generate"):
                logger_agent = WorkoutLogger()
                with st.spinner("BroCoach logging workout..."):
                    workout = logger_agent.chain.invoke({"input": uploaded_text})
                    st.session_state["workout_df"] = workout_to_dataframe(
                        workout=workout
                    )
                    st.dataframe(st.session_state["workout_df"],use_container_width=True)
            save_workout = st.button(
                "Save",
                use_container_width=True,
                disabled=("workout_df" not in st.session_state),
            )
            if save_workout:
                st.session_state["workout_df"].to_csv(
                    os.path.join(
                        WORKOUT_LOGS,
                        username,
                        f"{st.session_state['workout_df']['Date'].unique()[0]}.csv",
                    ),
                    index=False,
                )
                st.warning("Saved")

    with start_workout:
        start = st.button("Start")

    workouts = os.listdir(os.path.join(WORKOUT_LOGS, username))
    if len(workouts) != 0:
        selected_workout = st.selectbox("All workouts", workouts)
        st.dataframe(
            pd.read_csv(os.path.join(WORKOUT_LOGS, username, selected_workout)), use_container_width=True
        )
    else:
        st.error(f"No workout logged yet for {username}.")


def main():
    initialize_session_state()

    st.sidebar.title("User settings")
    page = st.sidebar.radio("Mode", ["Workout log", "Nutritionist"])
    username = st.sidebar.selectbox("Select user", ["dozo", "toubounou"])
    if page == "Nutritionist":
        chat_interface(username)
    elif page == "Workout log":
        workout_log_interface(username)

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



if __name__ == "__main__":
    main()
