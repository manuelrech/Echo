from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

from src.logger import setup_logger
from src.database.sql import SQLDatabase
from src.database.vector import ChromaDatabase
from src.tweets.creator import TweetCreator
from src.concepts.classes import Concept

logger = setup_logger(__name__)

tweet_concept = """
You are an expert in generating tweets for an X account of a ML/AI engineer.
Your audience is people into tech, data science, software engineering, and AI. Therefore tend to stay technical, without too many emojis. 
Use less than 280 characters for each tweet.
Include this link somewhere in the tweet: {link}

Generate a tweet about {concept_title}. 

Here you have a summary of the concept:
{concept_text}

Here you have some keywords that can help you generate the tweet:
{keywords}
"""

thread_concept = """
You are an expert in generating threads for an X account of a ML/AI engineer.
Your audience is people into tech, data science, software engineering, and AI. Therefore tend to stay technical, without too many emojis.
Use less than 280 characters for each tweet.
The first tweet should be catchy, ending with "A thread 🧵" to signal that there will be more tweets.
The others should be a deeper dive into the concept, with some technical details, do not be trivial.
Finish with a tweet thanking the reader for reading and inviting them to follow you for more.
Include this link somewhere in the thread: {link}

Generate a thread about {concept_title}. 

Here you have a summary of the concept:
{concept_text}

Here you have some keywords that can help you generate the tweet:
{keywords}
"""

def ask_user_for_generation_params() -> tuple[str, str | None]:
    """
    Asks the user if they want a tweet or thread,
    and whether they have extra instructions.
    """
    while True:
        user_choice = input("Do you want to generate a tweet or a thread? (1/2): ")
        if user_choice == '1':
            gen_type = 'tweet'
            break
        elif user_choice == '2':
            gen_type = 'thread'
            break
        else:
            print("Invalid input. Please enter '1' or '2'.")

    while True:
        extra_instructions_input = input("Do you want to add any extra instructions? (y/n): ")
        if extra_instructions_input == 'y':
            extra_instructions = input("Enter your extra instructions: ")
            break
        elif extra_instructions_input == 'n':
            extra_instructions = None
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    return gen_type, extra_instructions

def ask_for_tweet_publication() -> bool:
    """Ask user if they published the tweet and return their response."""
    while True:
        response = input("\nHave you published this tweet? (y/n): ").lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter 'y' or 'n'")

def generate_from_concept(db: SQLDatabase, vector_db: ChromaDatabase) -> None:
    """
    Fetches unused concepts, lets the user pick one, and then generates the tweet or thread.
    """
    concepts: list[dict] = db.get_unused_concepts_for_tweets(days_before=5)
    for index, concept in enumerate(concepts):
        print('\n\n')
        print(f"{concept['title']} - CONCEPT {index + 1}")
        print(concept['keywords'])
        print(concept['links'])
        print('- ' * 50)
        print(concept['concept_text'])
        print('_' * 100)

    # Let user select a concept
    while True:
        try:
            choice = int(input(f"Select a concept to generate a tweet (1-{len(concepts)}): "))
            if 1 <= choice <= len(concepts):
                selected_concept = concepts[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(concepts)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    gen_type, extra_instructions = ask_user_for_generation_params()

    # Retrieve similar concepts
    semantic_similar_docs = vector_db.get_similar_concepts(selected_concept)

    # Pick correct prompt template
    chosen_template = thread_concept if gen_type == 'thread' else tweet_concept

    creator = TweetCreator(db=db, prompt_template=chosen_template)
    thread_or_tweet = creator.generate_tweet(
        concept=selected_concept,
        similar_concepts=semantic_similar_docs,
        type=gen_type,
        extra_instructions=extra_instructions
    )
    
    if gen_type == 'tweet':
        print(thread_or_tweet)
        if ask_for_tweet_publication():
            db.mark_concept_as_used(concept_id=selected_concept['id'])
            print("Concept marked as used!")
    else:
        for tweet in thread_or_tweet.tweets:
            print('\n\n')
            print(tweet.text)
        if ask_for_tweet_publication():
            db.mark_concept_as_used(concept_id=selected_concept['id'])
            print("Concept marked as used!")

def main():
    logger.info("Starting tweet generation process...")
    db = SQLDatabase()
    vector_db = ChromaDatabase()
    generate_from_concept(db, vector_db)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)