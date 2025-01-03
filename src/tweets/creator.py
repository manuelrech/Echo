import os
from goose3.article import Article
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal
from goose3 import Goose

from ..logger import setup_logger
from ..database.sql import SQLDatabase

logger = setup_logger(__name__)

class Tweet(BaseModel):
    text: str = Field(..., description="The tweet text")

class Thread(BaseModel):
    tweets: list[Tweet] = Field(..., description="A list of tweets")

class TweetCreator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: SQLDatabase = Field(..., description='The database used')
    model_name: str = Field(default="gpt-4o")
    llm: ChatOpenAI = Field(default=None)
    prompt_template: str = Field(default="")

    def model_post_init(self, __context: Any) -> None:
        if 'deepseek' in self.model_name:
            self.llm = ChatOpenAI(model='deepseek-chat', api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        else:
            self.llm = ChatOpenAI(model=self.model_name, api_key=os.getenv("OPENAI_API_KEY"))
        return self
    
    def _extract_article_from_link(self, link: str) -> Article:
        g = Goose()
        article = g.extract(url=link)
        return article
    
    def _add_source_article(self, link: str) -> str:
        try:
            article = self._extract_article_from_link(link)
            self.prompt_template = self.prompt_template.replace("{link}", article.canonical_link)
            self.prompt_template = self.prompt_template + f"\n\nHere you can see the content of the original article:\n{article.cleaned_text}"
            if article.links:
                self.prompt_template = self.prompt_template + f"\n\nHere you can see the links related to the concept:\n{article.links}"
            return self.prompt_template

        except Exception as e:
            logger.error(f"Failed to extract article from link {link}: {e}", exc_info=True)
            return self.prompt_template
    
    def _add_similar_concepts(self, similar_concepts: list[dict]) -> str:
        for similar_concept in similar_concepts:
            self.prompt_template = self.prompt_template + f"\n\nHere you can see a similar concept:\n{similar_concept['document']}"
        return self.prompt_template

    def generate_tweet(self, concept: dict, similar_concepts: list[dict], extra_instructions: str, type: Literal['tweet', 'thread'] = 'tweet') -> Tweet | Thread:
        if extra_instructions:
            self.prompt_template = self.prompt_template + f"\n\nPay attention to the following:\n{extra_instructions}"
        
        if concept['links']:
            self.prompt_template = self._add_source_article(concept['links'])
        
        if similar_concepts:
            self.prompt_template = self._add_similar_concepts(similar_concepts)

        prompt = PromptTemplate.from_template(self.prompt_template)
        if type == 'tweet':
            chain = prompt | self.llm.with_structured_output(Tweet)
        else:
            chain = prompt | self.llm.with_structured_output(Thread)
        return chain.invoke(
            {
                "concept_title": concept['title'],
                "concept_text": concept['concept_text'],
                "keywords": concept['keywords'],
                "link": concept['links']
            }
        )
    