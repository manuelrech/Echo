import streamlit as st
from src.frontend.components.sidebar import show_api_keys, show_model_choice, show_prompt, show_error_details
from src.frontend.components.concepts import get_link_preview, show_keywords_as_pills
from src.frontend.api_client import EchoAPIClient
from src.backend.tweets.prompts import tweet_prompt, thread_prompt

def main():
    st.set_page_config(page_title="Generate Tweet - Echo", page_icon="🐦", layout="wide", initial_sidebar_state="collapsed", menu_items={'About': "Developed by Manuel Rech, https://www.x.com/RechManuel"})
    api_client = EchoAPIClient()
    api_client.set_user_id(st.session_state.user_id)

    with st.sidebar:
        st.header(f'Welcome, {api_client.get_username()}!')
        show_api_keys()
        show_model_choice()
        show_prompt(tweet_prompt, thread_prompt)

    if not st.session_state.current_concept:
        st.error("No concept selected. Please select a concept from the Concepts page.")
        if st.button("← Go back to Concepts"):
            st.switch_page("pages/1_📚_Explore_Concepts.py")
    else:
        concept = st.session_state.current_concept
        
        st.title(f"🐦 Generate Content")

        with st.container():
            st.subheader(concept['title'])
            
            if concept['keywords']:
                show_keywords_as_pills(concept['keywords'])
            
            st.markdown("---")
            st.markdown(concept['concept_text'])
            st.markdown("---")
            
            if concept.get('links'):
                links = concept['links'].split(',')
                for link in links:
                    link = link.strip()
                    if link:
                        preview = get_link_preview(link)
                        if preview:
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                                <img src="{preview['image']}" alt="Preview Image" style="width: 80px; height: 80px; margin-right: 10px; object-fit: cover; border-radius: 5px;">
                                <div>
                                    <h4 style="margin: 0;"><a href="{preview['url']}" target="_blank" style="text-decoration: none; color: #1f77b4;">{preview['title']}</a></h4>
                                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #555;">{preview['description']}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"Unable to fetch preview for {link}")

        col1, col2 = st.columns([1, 2])
        with col1:
            generation_type = st.radio(
                "Generation Type",
                ["Tweet", "Thread"],
                index=0 if st.session_state.get('generation_type') == 'tweet' else 1
            )
        
        with col2:
            if generation_type == "Thread":
                num_tweets = st.slider("Number of Tweets", min_value=3, max_value=10, value=5)
                st.caption("Including intro and closing tweets")
        
        extra_instructions = st.text_area(
            "Extra Instructions (optional)",
            placeholder="Add any specific instructions for the generation..."
        )
        
        # Single Generate button in full width
        if st.button("🚀 Generate", use_container_width=True, type="primary"):
            with st.spinner("Generating..."):
                try:
                    result = api_client.generate_tweet(
                        concept_id=concept['id'],
                        generation_type=generation_type.lower(),
                        num_tweets=num_tweets if generation_type == "Thread" else None,
                        extra_instructions=extra_instructions,
                        model_name=st.session_state.selected_model,
                        embedding_model_name=st.session_state.embedding_model_name
                    )
                    
                    st.markdown("### Generated Content:")
                    if generation_type == "Tweet":
                        st.markdown("""
                        <div style='
                            background-color: #f0f2f6;
                            padding: 20px;
                            border-radius: 10px;
                            border: 1px solid #e0e0e0;
                            margin: 10px 0;
                        '>
                            <div style='font-size: 1.1em; margin-bottom: 10px;'>%s</div>
                            <div style='color: #666; font-size: 0.9em;'>%d characters</div>
                        </div>
                        """ % (result['text'], len(result['text'])), unsafe_allow_html=True)
                    else:
                        for i, tweet in enumerate(result['tweets'], 1):
                            st.markdown(f"""
                            <div style='
                                background-color: #f0f2f6;
                                padding: 20px;
                                border-radius: 10px;
                                border: 1px solid #e0e0e0;
                                margin: 10px 0;
                            '>
                                <div style='color: #666; font-size: 0.9em; margin-bottom: 5px;'>Tweet {i}/{len(result['tweets'])}</div>
                                <div style='font-size: 1.1em; margin-bottom: 10px;'>{tweet['text']}</div>
                                <div style='color: #666; font-size: 0.9em;'>{len(tweet['text'])} characters</div>
                            </div>
                            """, unsafe_allow_html=True)

                except Exception as e:
                    show_error_details(e)

        # Add a small divider
        st.markdown("---")
        
        # Footer with navigation and actions
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back to Concepts", use_container_width=True):
                st.switch_page("pages/1_📚_Explore_Concepts.py")
        with col3:
            if st.button("Mark as Used & Exit 🗑️", use_container_width=True):
                if api_client.mark_concept_as_used(concept_id=concept['id']):
                    st.success("Concept marked as used!")
                    st.switch_page("pages/1_📚_Explore_Concepts.py")

if __name__ == "__main__":
    if st.session_state.get("logged_in", False):
        main()
    else:
        st.switch_page("Echo.py")