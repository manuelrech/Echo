import streamlit as st
from src.backend.database.sql import SQLDatabase

def check_password() -> bool:
    """Check if user provided correct login credentials."""
    def login_form() -> None:
        """Display login form with username and password inputs."""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered() -> None:
        """Validate entered password against stored credentials."""
        db = SQLDatabase()
        if db.verify_password(st.session_state["username"], st.session_state["password"]):
            user = db.get_user(username=st.session_state["username"])
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.session_state["chroma_collection_id"] = user["chroma_collection_id"]
            st.session_state["logged_in"] = True
            
            db.update_last_login(user["username"])
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("Welcome to Echo 👋")
    
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False