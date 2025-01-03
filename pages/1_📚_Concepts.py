import streamlit as st
from src.database.sql import SQLDatabase
from src.components.sidebar import show_api_keys, show_model_choice, show_email_fetching, show_concept_settings
from src.components.session_state import init_session_state
from src.components.concepts import get_unused_concepts, show_concept_details

st.set_page_config(page_title="Concepts - Echo", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

init_session_state()

with st.sidebar:
    show_api_keys()
    show_model_choice()
    show_concept_settings()
    show_email_fetching()


st.title("📚 Concepts")
db = SQLDatabase()
unused_concepts = db.get_unused_concepts_for_tweets(days_before=st.session_state.days_before) 

col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.keyword_filter = st.text_input(
        "🔍 Filter by keywords", 
        value=st.session_state.keyword_filter,
        help="Enter keywords to filter concepts. Separate multiple keywords with commas.")
with col2:
    sort_by = st.selectbox(
        "Sort by", 
        ["Most Recent", "Most Referenced"], 
        help="Choose how to sort the concepts")

if st.session_state.keyword_filter:
    unused_concepts, keywords_list = get_unused_concepts(
        keyword_filter=st.session_state.keyword_filter, 
        unused_concepts=unused_concepts
    )

if sort_by == "Most Referenced":
    unused_concepts = sorted(unused_concepts, key=lambda x: x['times_referenced'], reverse=True)
else:
    unused_concepts = sorted(unused_concepts, key=lambda x: x['updated_at'], reverse=True)

if not unused_concepts:
    if st.session_state.keyword_filter:
        st.info("No concepts found matching your filter. Try different keywords or clear the filter.")
    else:
        st.info("No unused concepts found. Try fetching some emails first!")
else:
    st.caption(f"Showing {len(unused_concepts)} concepts")
    
    cols = st.columns(3)
    for idx, concept in enumerate(unused_concepts):
        with cols[idx % 3]:
            with st.container():
                with st.container(height=350):
                    title_html = concept['title']
                    keywords_html = concept['keywords']
                    if st.session_state.keyword_filter:
                        for keyword in keywords_list:
                            title_html = title_html.replace(
                                keyword, 
                                f'<span style="background-color: #ffd70030">{keyword}</span>'
                            )
                            keywords_html = keywords_html.replace(
                                keyword, 
                                f'<span style="background-color: #ffd70030">{keyword}</span>'
                            )
                    
                    st.header(title_html)
                    st.write(concept.get('updated_at', 'Unknown date').split()[0].replace('-', '/') if concept.get('updated_at') != 'Unknown date' else 'Unknown date')
                    st.markdown(keywords_html, unsafe_allow_html=True)
                    st.write(f"Referenced: {concept.get('times_referenced', 0)} times")
                    if st.button("View Details 👀", key=f"view_{idx}", use_container_width=True):
                        show_concept_details(concept) 