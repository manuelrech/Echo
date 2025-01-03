import streamlit as st
import os

def init_session_state():
    if 'current_concept' not in st.session_state:
        st.session_state.current_concept = None
    if 'keyword_filter' not in st.session_state:
        st.session_state.keyword_filter = ""
    if 'days_before' not in st.session_state:
        st.session_state.days_before = 30
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "deepseek-v3"
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = os.getenv('OPENAI_API_KEY', '')
    if 'deepseek_key' not in st.session_state:
        st.session_state.deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
    if 'embedding_model_name' not in st.session_state:
        st.session_state.embedding_model_name = "text-embedding-ada-002"
