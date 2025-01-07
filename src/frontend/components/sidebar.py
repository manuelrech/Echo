import os
import streamlit as st
from src.frontend.api_client import EchoAPIClient

def show_error_details(error):
    """Display detailed error information in an expander."""
    print(error.response.json())
    with st.expander("🔍 Error Details", expanded=True):
        if hasattr(error, 'response') and error.response is not None:

            error_detail = error.response.json().get('detail', {})
            st.error(f"Error: {error_detail}")
        else:
            st.error(f"Error: {str(error)}")

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
        st.session_state.embedding_model_name = st.selectbox(
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
                try:
                    api_client = EchoAPIClient()
                    api_client.set_user_id(st.session_state.user_id)
                    recipient_list = [r.strip() for r in recipients.split('\n') if r.strip()]
                    
                    with st.spinner("Fetching emails and generating concepts..."):
                        result = api_client.fetch_and_generate_concepts(
                            model_name=st.session_state.selected_model,
                            embedding_model_name=st.session_state.embedding_model_name,
                            only_unread=unread_only,
                            recipients=recipient_list,
                            similarity_threshold=similarity_threshold
                        )

                        if 'too_many_emails' in result and result['too_many_emails']:
                            st.warning("I found more than 50 emails, I cannot fetch that many in the demo version\n\nTry setting a list of recipients or tick the 'Only Unread' checkbox.")
                        elif 'no_emails_found' in result and result['no_emails_found']:
                            st.warning("No emails found.\n\nTry unchecking the 'Only Unread' checkbox and inserting a list of recipients.")
                        else:
                            st.success(
                                f"Successfully processed {result['processed_emails']} emails "
                                f"and generated {result['processed_concepts']} concepts!"
                            )
                except Exception as e:
                    # raise e
                    show_error_details(e)
