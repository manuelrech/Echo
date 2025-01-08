import streamlit as st
from dotenv import load_dotenv, find_dotenv
from src.frontend.components.session_state import init_session_state
from src.frontend.components.login import check_password
from src.frontend.api_client import EchoAPIClient
import requests

load_dotenv(find_dotenv())

st.set_page_config(
        page_title="Echo - Tweet Generator",
        page_icon="🐦",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'About': "Developed by Manuel Rech, https://www.x.com/RechManuel"
        }
    )

def main():

    init_session_state()
    api_client = EchoAPIClient()
    api_client.set_user_id(st.session_state.user_id)

    try:
        st.sidebar.header(f"Welcome, {api_client.get_username()}!")
    except requests.exceptions.ConnectionError as e:
        st.error("Failed to connect to the API. Please check your internet connection and make sure backend is running.")
        st.stop()
        # show_api_keys()

    st.markdown("""
        <div style='
            background: linear-gradient(45deg, #1DA1F2, #14171A);
            padding: 40px;
            border-radius: 20px;
            color: white;
            font-size: 28px;
            font-weight: 600;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(29, 161, 242, 0.3);
            transform: translateY(0);
            transition: all 0.4s ease;
            cursor: pointer;
        ' onmouseover="this.style.transform='translateY(-10px)'" onmouseout="this.style.transform='translateY(0)'">
            <div style="font-size: 1.2em; margin-bottom: 10px;">Want to grow your audience by posting quality tweets,</div>
            <div style="font-size: 1.5em; font-weight: bold;">But don't have the time to curate content? 🚀</div>
        </div>

        <div style='
            text-align: center;
            padding: 30px;
            margin: 30px 0;
        '>
            <h1 style='
                text-transform: uppercase;
                letter-spacing: 3px;
                font-weight: 900;
                font-size: 6em;
                background: linear-gradient(90deg, #1DA1F2 0%, #14171A 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.2);
            '>
                Welcome to Echo
            </h1>
        </div>

        <div style="font-size: 20px; line-height: 1.8; text-align: center; margin: 20px;">
            <p>✨ <strong>Transform newsletters into inspiration:</strong> Extracts the key concepts from your favorite emails.</p>
            <p>🔍 <strong>Optimize for engagement:</strong> Organizes and refines ideas with smart analysis tools.</p>
            <p>🚀 <strong>Create impactful tweets in a click:</strong> Generates captivating posts and threads effortlessly.</p>
        </div>

        <style>
            .stButton > button {
                font-size: 18px;
                padding: 12px 20px;
                border-radius: 10px;
                background: linear-gradient(45deg, #1DA1F2, #14171A);
                color: white;
                border: none;
                cursor: pointer;
                transition: background 0.3s ease, transform 0.3s ease;
            }
            .stButton > button:hover {
                background: linear-gradient(45deg, #14171A, #1DA1F2);
                transform: scale(1.05);
            }
            a {
                color: #1DA1F2;
                text-decoration: none;
                font-weight: bold;
                transition: color 0.3s ease, text-decoration 0.3s ease;
            }
            a:hover {
                color: #0a7cbf;
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 Browse Concepts", use_container_width=True):
            st.switch_page("pages/1_📚_Explore_Concepts.py")
    with col2:
        if st.button("🐦 Generate Tweets", use_container_width=True):
            st.switch_page("pages/2_🐦_Generate_Tweet.py")

    st.markdown("<p class='caption'>Need help? <a href='https://www.x.com/RechManuel'>Contact me</a>.</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    if st.session_state.get("logged_in", False):
        main()
    else:
        if not check_password():
            st.stop()
        else:
            st.session_state["logged_in"] = True
            main()