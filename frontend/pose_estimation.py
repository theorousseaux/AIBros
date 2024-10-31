import streamlit as st
import sys
import os
import cv2

sys.path.append(os.getcwd())
from src.pose_estimation.estimator import model
from frontend.utils import save_uploaded_file


############ Main ############

st.title("Pose Estimation")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Choose an file...", type=["jpg", "jpeg", "png", "mp4", "avi", "mov"]
    )

if uploaded_file is not None:
    with col1:
        apply_button = st.button("Apply Pose Estimation")

    if apply_button:
        file_path = save_uploaded_file(uploaded_file)
        # The file is an image
        if uploaded_file.name.endswith(("jpg", "jpeg", "png")):
            results = model(source=file_path)
            img = results[0].plot()
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            with col2:
                st.image(img_rgb, use_column_width=True)

        # The file is a video
        else:
            results = model(source=st.session_state["file_path"])
