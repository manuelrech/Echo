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
        self.llm = ChatOpenAI(model=self.model_name, api_key=os.getenv("OPENAI_API_KEY"))
        return self
    
    def _add_source_article(self, link: str) -> str:
        article = self._extract_article_from_link(link)
        return self.prompt_template + f"\n\nHere you can see a the content of the original article:\n{article}"
    
    def _extract_article_from_link(self, link: str) -> Article:
        g = Goose()
        article = g.extract(url=link)
        return article

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
    
    
    def generate_tweet_from_external_source(self, link: str, extra_instructions: str, type: Literal['tweet', 'thread'] = 'tweet') -> Tweet | Thread:
        article = self._extract_article_from_link(link)
        if extra_instructions:
            self.prompt_template = self.prompt_template + f"\n\nPay attention to the following:\n{extra_instructions}"
        prompt = PromptTemplate.from_template(self.prompt_template)
        if type == 'tweet':
            chain = prompt | self.llm.with_structured_output(Tweet)
        else:
            chain = prompt | self.llm.with_structured_output(Thread)
        return chain.invoke(
            {
                "article": article.cleaned_text,
                "initial_link": link,
                "links_found": article.links
            }
        )
    