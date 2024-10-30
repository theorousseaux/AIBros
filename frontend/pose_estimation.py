import streamlit as st
import sys
import os
import cv2

sys.path.append(os.getcwd())
from src.pose_estimation.estimator import model
from frontend.utils import save_uploaded_file

if "file_path" not in st.session_state:
    st.session_state["file_path"] = None

############ Main ############

st.title("Pose Estimation")

uploaded_file = st.file_uploader("Choose an image...", type="jpg")

if uploaded_file is not None:
    st.session_state["file_path"] = save_uploaded_file(uploaded_file)

if st.session_state["file_path"] is not None:

    col1, col2 = st.columns(2)
    with col1:
        st.image(st.session_state["file_path"], use_column_width=True)

        apply_button = st.button("Apply Pose Estimation")

    if apply_button:
        with col2:
            results = model(source=st.session_state["file_path"])
            img = results[0].plot()
            # Conversion de BGR à RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            st.image(img_rgb, use_column_width=True)
