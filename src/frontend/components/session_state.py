import streamlit as st
import os
from ...backend.tweets.prompts import tweet_header_prompt, thread_header_prompt
from ...frontend.api_client import EchoAPIClient

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "chroma_collection_id" not in st.session_state:
        st.session_state["chroma_collection_id"] = None
    
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
 
    if st.session_state.logged_in and st.session_state.user_id:
        try:
            api_client = EchoAPIClient()
            api_client.set_user_id(st.session_state.user_id)
            prompts = api_client.get_prompts()
            if prompts:
                st.session_state.tweet_prompt = prompts['tweet_prompt']
                st.session_state.thread_prompt = prompts['thread_prompt']
            else:
                if 'tweet_prompt' not in st.session_state:
                    st.session_state.tweet_prompt = tweet_header_prompt
                if 'thread_prompt' not in st.session_state:
                    st.session_state.thread_prompt = thread_header_prompt
        except Exception:
            if 'tweet_prompt' not in st.session_state:
                st.session_state.tweet_prompt = tweet_header_prompt
            if 'thread_prompt' not in st.session_state:
                st.session_state.thread_prompt = thread_header_prompt
    else:
        if 'tweet_prompt' not in st.session_state:
            st.session_state.tweet_prompt = tweet_header_prompt
        if 'thread_prompt' not in st.session_state:
            st.session_state.thread_prompt = thread_header_prompt