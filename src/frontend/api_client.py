import os
import requests
from typing import Dict, List, Optional
from streamlit import cache_data

class EchoAPIClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or 
                        os.getenv('BACKEND_URL', 'http://localhost:8000')).rstrip('/')
        self._user_id: Optional[int] = None

    @property
    def user_id(self) -> int:
        """Get the current user ID."""
        if self._user_id is None:
            raise ValueError("User ID not set. Call set_user_id() first.")
        return self._user_id

    def set_user_id(self, user_id: int) -> None:
        """Set the user ID for subsequent requests."""
        self._user_id = user_id

    def fetch_and_generate_concepts(self,
                                  model_name: str,
                                  embedding_model_name: str,
                                  only_unread: bool = True,
                                  recipients: List[str] = [],
                                  similarity_threshold: float = 0.85) -> Dict:
        data = {
            "user_id": self.user_id,
            "only_unread": only_unread,
            "recipients": recipients,
            "similarity_threshold": similarity_threshold,
            "model_name": model_name,
            "embedding_model_name": embedding_model_name
        }
        response = requests.post(f"{self.base_url}/fetch-and-generate-concepts?user_id={self.user_id}", json=data)
        response.raise_for_status()
        return response.json()

    def get_unused_concepts(self, days_before: int = 30) -> List[Dict]:
        response = requests.get(
            f"{self.base_url}/concepts/unused",
            params={"days_before": days_before, "user_id": self.user_id}
        )
        response.raise_for_status()
        return response.json()
    
    def get_username(self) -> str:
        response = requests.get(
            f"{self.base_url}/user/username",
            params={"user_id": self.user_id}
        )
        response.raise_for_status()
        return response.json()

    def get_concept(self, concept_id: int) -> Dict:
        response = requests.get(
            f"{self.base_url}/concepts/{concept_id}",
            params={"user_id": self.user_id}
        )
        response.raise_for_status()
        return response.json()

    def generate_tweet(self, 
                      concept_id: int,
                      generation_type: str,
                      model_name: str,
                      embedding_model_name: str,
                      prompt: str,
                      num_tweets: Optional[int] = 5,
                      extra_instructions: Optional[str] = None,
                      ) -> Dict:
        data = {
            "user_id": self.user_id,
            "concept_id": concept_id,
            "generation_type": generation_type,
            "num_tweets": num_tweets,
            "extra_instructions": extra_instructions,
            "model_name": model_name,
            "embedding_model_name": embedding_model_name,
            "prompt": prompt
        }
        response = requests.post(f"{self.base_url}/generate-tweet?user_id={self.user_id}", json=data)
        response.raise_for_status()
        return response.json()

    def mark_concept_as_used(self, concept_id: int) -> Dict:
        response = requests.post(
            f"{self.base_url}/concepts/{concept_id}/mark-used",
            params={"user_id": self.user_id}
        )
        response.raise_for_status()
        return response.json()

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user's password."""
        response = requests.post(
            f"{self.base_url}/auth/verify",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["verified"]

    def register_user(self, username: str, password: str) -> Optional[int]:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["user_id"]

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user information by username."""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                params={"username": username}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        response = requests.get(
            f"{self.base_url}/user/exists",
            params={"username": username}
        )
        response.raise_for_status()
        return response.json()["exists"]

    def update_last_login(self, username: str) -> bool:
        """Update user's last login timestamp."""
        response = requests.post(
            f"{self.base_url}/user/login",
            params={"username": username}
        )
        response.raise_for_status()
        return response.json()["success"]

    def save_prompts(self, tweet_prompt: str, thread_prompt: str) -> bool:
        """Save prompts for the current user."""
        response = requests.post(
            f"{self.base_url}/prompts/save?user_id={self.user_id}",
            params={
                "user_id": self.user_id,
                "tweet_prompt": tweet_prompt,
                "thread_prompt": thread_prompt
            }
        )
        response.raise_for_status()
        return response.json()["success"]

    def get_prompts(self) -> Optional[Dict]:
        """Get prompts for the current user."""
        try:
            response = requests.get(
                f"{self.base_url}/prompts?user_id={self.user_id}",
                params={"user_id": self.user_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def process_mbox_file(
        self,
        file,
        model_name: str,
        embedding_model_name: str,
        similarity_threshold: float = 0.85
    ) -> dict:
        """Process an uploaded .mbox file and generate concepts."""
        files = {"file": file}
        data = {
            "model_name": model_name,
            "embedding_model_name": embedding_model_name,
            "similarity_threshold": similarity_threshold
        }
        
        response = requests.post(
            f"{self.base_url}/process-mbox-file?user_id={self.user_id}",
            files=files,
            data=data
        )
        return response.json() 