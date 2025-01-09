import requests
import streamlit as st
from src.frontend.api_client import EchoAPIClient

def get_link_preview(url):
    response = requests.get(f"https://api.microlink.io/?url={url}")
    if response.status_code == 200:
        data = response.json().get('data', {})
        image = data.get('image', {})
        image_url = image.get('url', '') if image else ''
        return {
            'title': data.get('title', 'No title available'),
            'description': data.get('description', 'No description available'),
            'image': image_url,
            'url': url
        }
    return None

def show_keywords_as_pills(keywords):
    keywords_list = [k.strip() for k in keywords.split(',')]
    cols = st.columns(len(keywords_list))
    for idx, keyword in enumerate(keywords_list):
        with cols[idx]:
            st.markdown(
                f"""
                <div style='background-color: #1f77b420; padding: 0.5rem; border-radius: 5px; text-align: center; margin: 0.2rem'>
                    {keyword}
                </div>
                """,
                unsafe_allow_html=True
            )

@st.dialog(title='Concept Details', width="large")
def show_concept_details(concept):
    st.title(concept['title'])
    
    if concept['keywords']:
        show_keywords_as_pills(concept['keywords'])
    
    st.markdown("---")
    st.markdown(concept['concept_text'])
    st.markdown("---")
    
    if concept.get('links'):
        st.markdown("### Source Links")
        links = concept['links'].split(',')
        for link in links:
            link = link.strip()
            if link:  # Only process non-empty links
                preview = get_link_preview(link)
                if preview:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px; background-color: white;">
                        <img src="{preview['image']}" alt="Preview Image" style="width: 80px; height: 80px; margin-right: 10px; object-fit: cover; border-radius: 5px;">
                        <div>
                            <h4 style="margin: 0;"><a href="{preview['url']}" target="_blank" style="text-decoration: none; color: #1f77b4;">{preview['title']}</a></h4>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #555;">{preview['description']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"🔗 [{link}]({link})")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Tweet 🐦", use_container_width=True):
            st.session_state.generation_type = 'tweet'
            st.session_state.current_concept = concept
            st.switch_page("pages/2_🐦_Generate_Tweet.py")
    with col2:
        if st.button("Mark as Used 🗑️", use_container_width=True):
            api_client = EchoAPIClient()
            api_client.set_user_id(st.session_state.user_id)
            if api_client.mark_concept_as_used(concept_id=concept['id']):
                st.success("Concept marked as used!")
                st.rerun()

def filter_concepts(keyword_filter: str, unused_concepts: list[dict]) -> list[dict]:
    keywords_list = [k.strip().lower() for k in keyword_filter.split(",")]
    unused_concepts = [
        concept for concept in unused_concepts
        if any(keyword in concept['keywords'].lower() or keyword in concept['title'].lower() 
               for keyword in keywords_list)
    ]
    return unused_concepts, keywords_list