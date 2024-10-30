import os
import streamlit as st

def save_uploaded_file(uploaded_file):
    try:
        file_path = os.path.join('src', 'pose_estimation', 'file_uploaded', uploaded_file.name)
        par_dir = os.path.dirname(file_path)
        if not os.path.exists(par_dir):
            os.makedirs(par_dir, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        return file_path
    except Exception as e:
        st.error(f"Error: {e}")
        return None