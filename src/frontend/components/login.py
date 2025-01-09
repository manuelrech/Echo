import streamlit as st
from src.frontend.api_client import EchoAPIClient

def check_password() -> bool:
    """Check if user provided correct login credentials."""
    def login_form() -> None:
        """Display login form with username and password inputs."""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.markdown('Forgot password? Contact me at [@RechManuel](https://www.x.com/RechManuel)')
            st.form_submit_button("Log in", on_click=password_entered)
            
    def register_form() -> None:
        """Display registration form with username and password inputs."""
        with st.form("Registration"):
            st.text_input("Username", key="reg_username")
            st.text_input("Password", type="password", key="reg_password")
            st.text_input("Confirm Password", type="password", key="reg_password_confirm")
            st.form_submit_button("Register", on_click=register_user)

    def register_user() -> None:
        """Create a new user with the provided credentials."""
        if st.session_state["reg_password"] != st.session_state["reg_password_confirm"]:
            st.session_state["registration_error"] = "Passwords do not match"
            return
            
        client = EchoAPIClient()
        # Check if user already exists
        if client.user_exists(st.session_state["reg_username"]):
            st.session_state["registration_error"] = "Username already exists"
            return
            
        user_id = client.register_user(st.session_state["reg_username"], st.session_state["reg_password"])
        if user_id:
            st.session_state["registration_success"] = True
            # Clear registration fields
            del st.session_state["reg_username"]
            del st.session_state["reg_password"]
            del st.session_state["reg_password_confirm"]
        else:
            st.session_state["registration_error"] = "Error creating user"

    def password_entered() -> None:
        """Validate entered password against stored credentials."""
        client = EchoAPIClient()
        if client.verify_password(st.session_state["username"], st.session_state["password"]):
            user = client.get_user(username=st.session_state["username"])
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.session_state["chroma_collection_id"] = user["chroma_collection_id"]
            st.session_state["logged_in"] = True
            
            client.update_last_login(user["username"])
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("Welcome to Echo 👋")
    
    # Toggle between login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_form()
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 User not known or password incorrect")
            
    with tab2:
        register_form()
        if "registration_error" in st.session_state:
            st.error(st.session_state["registration_error"])
            del st.session_state["registration_error"]
        if "registration_success" in st.session_state:
            st.success("✅ Registration successful! You can now log in.")
            del st.session_state["registration_success"]
    
    return False