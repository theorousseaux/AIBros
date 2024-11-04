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
from PIL import Image
from io import BytesIO

st.set_page_config(layout="wide")


def workout_log_interface(username):
    st.title(f"Logger")
    upload_workout = st.expander(
        "Upload an existing workout (text or image)", expanded=True
    )

    if "logged_workouts" not in st.session_state:
        st.session_state["logged_workouts"] = pd.DataFrame()
    with upload_workout:
        col1, col2 = st.columns([0.7, 0.3])
        upload_mode = col1.radio(
            "Format", ["From Image Folder", "Upload Photos", "Text"]
        )
        notes_img = None
        notes_text = None
        if upload_mode == "Upload Photos":
            notes_img_up = col1.file_uploader(
                "Photograph of your workout notes", accept_multiple_files=True
            )
            img_names = [img.name for img in notes_img_up]
            if notes_img_up is not None and len(img_names) != 0:
                tabs = col2.tabs(img_names)
                for i in range(len(notes_img_up)):
                    tabs[i].image(notes_img_up[i], width=500)
            notes_img = [note.read() for note in notes_img_up]
        elif upload_mode == "Text":
            notes_text = st.text_area("Notes of your workout")
        elif upload_mode == "From Image Folder":
            img_folder = col1.text_input(
                "URL of the folder containing the images of workout notes",
                value=Path(os.path.join(os.getcwd(), "data", "notes_training")),
            )
            img_names = os.listdir(img_folder)
            notes_img_paths = [
                os.path.join(img_folder, img_name) for img_name in img_names
            ]
            if notes_img_paths is not None:
                tabs = col2.tabs(img_names)
                for i in range(len(notes_img_paths)):
                    tabs[i].image(notes_img_paths[i], width=500)
            notes_img = []
            for note_img_p in notes_img_paths:
                with open(note_img_p, "rb") as file:
                    notes_img.append(file.read())
        if col1.button("Generate"):
            logger_agent = WorkoutLogger()

            with st.spinner("BroCoach logging workout..."):
                if notes_img is not None:
                    df_tabs = col1.tabs(img_names)
                    for i in range(len(notes_img)):
                        workout = logger_agent.generate(
                            input_text=notes_text, input_img=notes_img[i]
                        )
                        st.write(
                            f"Nb de tokens input : {len(str(logger_agent.prompt))/4}"
                        )
                        st.write(f"Nb de tokens output : {len(str(workout))/4}")
                        st.session_state[img_names[i]] = workout_to_dataframe(
                            workout=workout
                        )
                        df_tabs[i].dataframe(
                            st.session_state[img_names[i]], use_container_width=True
                        )
                        st.session_state["logged_workouts"] = add_workout_to_dataframe(
                            workout=workout,
                            df=st.session_state["logged_workouts"],
                        )
                else:
                    workout = logger_agent.generate(input_text=notes_text)
                    workout_df = workout_to_dataframe(workout=workout)
                    st.session_state["logged_workouts"] = add_workout_to_dataframe(
                        workout=workout,
                        df=st.session_state["logged_workouts"],
                    )

        st.markdown("## Full log preview")
        st.dataframe(
            st.session_state["logged_workouts"],
            use_container_width=True,
            height=800,
        )
        save_workout = st.button(
            "Save",
            use_container_width=True,
            # disabled=("workout_df" not in st.session_state),
        )
        if save_workout:
            csv_path = os.path.join(
                WORKOUT_LOGS,
                f"{username}.csv",
            )
            file_exists = os.path.isfile(csv_path)
            st.session_state["logged_workouts"].to_csv(
                csv_path,
                mode="a",
                index=False,
                header=not file_exists,
            )
            st.warning("Saved")

    # start_workout = st.expander("Start a fresh new workout")
    # with start_workout:
    #     start = st.button("Start")
    # os.makedirs(os.path.join(WORKOUT_LOGS, username), exist_ok=True)
    # workouts = os.listdir(os.path.join(WORKOUT_LOGS, username))
    workout_log_path = os.path.join(WORKOUT_LOGS, f"{username}.csv")
    if os.path.isfile(workout_log_path):
        workout_log = pd.read_csv(workout_log_path)
        st.dataframe(
            workout_log,
            use_container_width=True,
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
