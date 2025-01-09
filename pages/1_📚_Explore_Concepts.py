import streamlit as st
from src.frontend.components.sidebar import show_api_keys, show_model_choice, show_email_fetching, show_concept_settings
from src.frontend.components.concepts import get_unused_concepts, show_concept_details
from src.frontend.api_client import EchoAPIClient

def main():
    st.set_page_config(page_title="Concepts - Echo", page_icon="📚", layout="wide", initial_sidebar_state="collapsed", menu_items={'About': "Developed by Manuel Rech, https://www.x.com/RechManuel"})
    api_client = EchoAPIClient()
    api_client.set_user_id(st.session_state.user_id)

    with st.sidebar:
        st.header(f"Welcome, {api_client.get_username()}!")
        # show_api_keys()
        show_model_choice()
        show_concept_settings()
        show_email_fetching()

    st.title("📚 Explore Concepts")
    
    unused_concepts = api_client.get_unused_concepts(days_before=st.session_state.days_before)

    col1, col2, col3 = st.columns([6, 2, 1])
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
    with col3:
        n_cols = st.number_input("Columns", value=3, min_value=1, max_value=10, step=1, help="Number of columns to display the concepts in")

    if st.session_state.keyword_filter:
        unused_concepts, keywords_list = get_unused_concepts(
            keyword_filter=st.session_state.keyword_filter, 
            unused_concepts=unused_concepts
        )

    if sort_by == "Most Referenced":
        unused_concepts = sorted(unused_concepts, key=lambda x: x['times_referenced'], reverse=True)
    else:
        unused_concepts = sorted(unused_concepts, key=lambda x: x['date'], reverse=True)

    if not unused_concepts:
        if st.session_state.keyword_filter:
            st.info("No concepts found matching your filter. Try different keywords or clear the filter.")
        else:
            st.info("No unused concepts found. Try fetching some emails first!")
    else:
        st.caption(f"Showing {len(unused_concepts)} concepts")
        
        cols = st.columns(n_cols)
        for idx, concept in enumerate(unused_concepts):
            with cols[idx % n_cols]:
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
                        st.write(concept.get('date', 'Unknown date').split()[0].replace('-', '/') if concept.get('date') != 'Unknown date' else 'Unknown date')
                        st.markdown(keywords_html, unsafe_allow_html=True)
                        st.write(f"Referenced: {concept.get('times_referenced', 0)} times")
                        if st.button("View Details 👀", key=f"view_{idx}", use_container_width=True):
                            show_concept_details(concept)

if __name__ == "__main__":
    if st.session_state.get("logged_in", False):
        main()
    else:
        st.switch_page("Echo.py")