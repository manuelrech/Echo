import streamlit as st
import os
from src.database.sql import SQLDatabase
from src.database.vector import ChromaDatabase
from src.concepts.extractor import ConceptExtractor
from src.gmail_reader.email_fetcher import EmailFetcher

def show_api_keys():
    """Show API keys expander in sidebar."""
    with st.expander("🔑 API Keys"):
        openai_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.get('openai_key', ''),
            type="password"
        )
        deepseek_key = st.text_input(
            "DeepSeek API Key",
            value=st.session_state.get('deepseek_key', ''),
            type="password"
        )
        if openai_key:
            os.environ['OPENAI_API_KEY'] = openai_key
            st.session_state.openai_key = openai_key 
        if deepseek_key:
            os.environ['DEEPSEEK_API_KEY'] = deepseek_key
            st.session_state.deepseek_key = deepseek_key
    
    
def show_model_choice():
    with st.expander("🤖 Model Settings"):
        st.session_state.selected_model = st.selectbox(
            "Select Model",
            ["deepseek-v3", "gpt-4o",  "gpt-4o-mini"],
            help="Choose the model to use for generation"
        )
        st.session_state.selected_embedding_model = st.selectbox(
            "Select Embedding Model",
            ["text-embedding-ada-002"],
            help="Choose the embedding model to use for generation"
        )

def show_prompt(tweet_prompt, thread_prompt) -> int:
    with st.expander("🔍 Prompts"):
        st.markdown("### Tweet Prompt")
        st.code(tweet_prompt, language="text")
        st.markdown("### Thread Prompt")
        st.code(thread_prompt, language="text")

def show_concept_settings():
    with st.expander(label="🔍 Concept Settings"):
        st.session_state.days_before = st.slider(
            "Days before",
            min_value=0,
            max_value=30,
            value=30,
            step=1,
            help="How many days before to fetch emails"
        )

def show_email_fetching():
    with st.form("email_fetching"):
        st.subheader("Email Fetching")
        unread_only = st.checkbox("Only Unread Emails", value=True)
        recipients = st.text_area(
            "Email Recipients (one per line)",
            help="Enter email addresses to filter by, one per line"
        )
        similarity_threshold = st.slider(
            "Concept Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.01,
            help="Higher values mean stricter uniqueness check for concepts"
        )
        
        if st.form_submit_button("Fetch Emails & Generate Concepts"):
            if not st.session_state.openai_key and not st.session_state.deepseek_key:
                st.error("Please set your OpenAI or DeepSeek API key first!")
            else:
                db = SQLDatabase()
                vector_db = ChromaDatabase(
                    embedding_model_name=st.session_state.selected_embedding_model,
                )
                email_fetcher = EmailFetcher()
                concept_extractor = ConceptExtractor(
                    sql_db=db,
                    vector_db=vector_db,
                    model=st.session_state.selected_model,
                )
                try:
                    with st.spinner("Fetching emails..."):
                        recipient_list = [r.strip() for r in recipients.split('\n') if r.strip()]
                        
                        messages = email_fetcher.list_messages(
                            only_unread=unread_only,
                            recipients=recipient_list if recipient_list else []
                        )
                        
                        for message in messages:
                            raw_message = email_fetcher.get_raw_message('me', message['id'])
                            formatted_message = email_fetcher.format_message(raw_message)
                            db.store_email(formatted_message)
                        
                    with st.spinner("Generating concepts..."):
                        emails = db.get_unprocessed_emails()
                        
                        for email in emails:
                            concept_extractor.process_email_concepts(email, similarity_threshold)
                        
                        st.success(f"Successfully processed {len(emails)} emails!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
