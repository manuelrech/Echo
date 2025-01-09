from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from src.backend.database.sql import SQLDatabase
from src.backend.database.vector import ChromaDatabase
from src.backend.tweets.creator import TweetCreator
from src.backend.gmail_reader.email_fetcher import EmailFetcher
from src.backend.gmail_loader.email_loader import EmailLoader
from src.backend.concepts.extractor import ConceptExtractor
from src.backend.logger import setup_logger
from src.backend.schemas.api import (
    TweetRequest, 
    EmailFetchRequest, 
    UserAuth, 
    UserResponse,
    MboxUploadRequest
)
import traceback
import tempfile
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = setup_logger(__name__)

app = FastAPI(title="Echo API", version="1.0.0")

async def get_current_user_id(user_id: int) -> int:
    """Dependency to get the current user ID from the request."""
    if not user_id or user_id <= 0:
        raise HTTPException(status_code=401, detail="Valid user_id is required")
    return user_id

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_detail = {
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }
    logger.error(f"Error occurred: {error_detail}")
    return JSONResponse(
        status_code=500,
        content={"detail": error_detail}
    )

@app.post("/fetch-and-generate-concepts")
async def fetch_and_generate_concepts(request: EmailFetchRequest, user_id: int = Depends(get_current_user_id)):
    try:
        logger.info(f"Fetching and generating concepts with request: {request}")
        db = SQLDatabase()
        
        user = db.get_user(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chroma_collection_id = user["chroma_collection_id"]
        
        vector_db = ChromaDatabase(
            embedding_model_name=request.embedding_model_name,
            collection_name=chroma_collection_id
        )
        logger.info("Fetching and generating concepts")
        email_fetcher = EmailFetcher(user_id=user_id)
        concept_extractor = ConceptExtractor(
            sql_db=db,
            vector_db=vector_db,
            model=request.model_name,
        )
        logger.info("Fetching emails")

        messages = email_fetcher.list_messages(
            only_unread=request.only_unread,
            recipients=request.recipients
        )
        if len(messages) > 50:
            logger.warning("I found more than 50 emails")
            return {"status": "success", "fetched_emails": len(messages), "too_many_emails": True}

        if len(messages) == 0:
            logger.warning("No emails found")
            return {"status": "success", "no_emails_found": True}
        
        processed_emails = 0
        for message in messages:
            raw_message = email_fetcher.get_raw_message('me', message['id'])
            formatted_message = email_fetcher.format_message(raw_message)
            db.store_email(formatted_message, user_id)
            processed_emails += 1

        emails = db.get_unprocessed_emails(user_id)
        processed_concepts = 0
        for email in emails:
            success, stored_count = concept_extractor.process_email_concepts(
                email, 
                request.similarity_threshold, 
                user_id,
                chroma_collection_id
            )
            if success:
                processed_concepts += stored_count

        return {
            "status": "success",
            "processed_emails": processed_emails,
            "processed_concepts": processed_concepts
        }

    except Exception as e:
        logger.error(f"Error in fetch_and_generate_concepts: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/concepts/unused")
async def get_unused_concepts(days_before: int = 30, user_id: int = Depends(get_current_user_id)):
    try:
        db = SQLDatabase()
        concepts = db.get_unused_concepts_for_tweets(user_id=user_id, days_before=days_before)
        if not concepts:
            return []
        return concepts
    except Exception as e:
        logger.error(f"Error in get_unused_concepts: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/concepts/{concept_id}")
async def get_concept(concept_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        db = SQLDatabase()
        concept = db.get_concept_by_id(concept_id, user_id)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        return concept
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_concept: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/generate-tweet")
async def generate_tweet(request: TweetRequest, user_id: int = Depends(get_current_user_id)):
    try:
        db = SQLDatabase()
        
        user = db.get_user(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        chroma_collection_id = user["chroma_collection_id"]
        
        concept = db.get_concept_by_id(request.concept_id, user_id)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        vector_db = ChromaDatabase(
            embedding_model_name=request.embedding_model_name,
            collection_name=chroma_collection_id
        )
        similar_concepts = vector_db.get_similar_concepts(
            concept=concept,
            similarity_threshold=0.85,
            user_collection_id=chroma_collection_id
        )

        if request.generation_type == "thread":
            modified_prompt = request.prompt.replace("{num_tweets}", str(request.num_tweets))
            creator = TweetCreator(
                prompt_template=modified_prompt,
                model_name=request.model_name
            )
        else:
            creator = TweetCreator(
                prompt_template=request.prompt,
                model_name=request.model_name
            )

        result = creator.generate_tweet(
            concept=concept,
            similar_concepts=similar_concepts,
            type=request.generation_type.lower(),
            extra_instructions=request.extra_instructions,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_tweet: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/concepts/{concept_id}/mark-used")
async def mark_concept_as_used(concept_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        db = SQLDatabase()
        # First verify the concept belongs to the user
        concept = db.get_concept_by_id(concept_id, user_id)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
            
        success = db.mark_concept_as_used(concept_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to mark concept as used")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_concept_as_used: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail) 

@app.get("/user/username")
async def get_username(user_id: int = Depends(get_current_user_id)):
    db = SQLDatabase()
    user = db.get_user(user_id=user_id)
    return user["username"]

@app.get("/user/exists")
async def check_user_exists(username: str):
    """Check if a user exists."""
    try:
        db = SQLDatabase()
        user = db.get_user(username=username)
        return {"exists": user is not None}
    except Exception as e:
        logger.error(f"Error in check_user_exists: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/verify")
async def verify_password(auth: UserAuth):
    """Verify user's password."""
    try:
        db = SQLDatabase()
        is_valid = db.verify_password(auth.username, auth.password)
        return {"verified": is_valid}
    except Exception as e:
        logger.error(f"Error in verify_password: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register")
async def register_user(auth: UserAuth):
    """Register a new user."""
    try:
        db = SQLDatabase()
        # Check if user already exists
        if db.get_user(username=auth.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        user_id = db.create_user(auth.username, auth.password)
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        return {"user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user")
async def get_user(username: str):
    """Get user information by username."""
    try:
        db = SQLDatabase()
        user = db.get_user(username=username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user["id"],
            username=user["username"],
            chroma_collection_id=user["chroma_collection_id"],
            created_at=user["created_at"],
            last_login=user["last_login"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/login")
async def update_last_login(username: str):
    """Update user's last login timestamp."""
    try:
        db = SQLDatabase()
        success = db.update_last_login(username)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update last login")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in update_last_login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prompts/save")
async def save_prompts(tweet_prompt: str, thread_prompt: str, user_id: int = Depends(get_current_user_id)):
    """Save prompts for a user."""
    try:
        db = SQLDatabase()
        success = db.save_prompts(user_id, tweet_prompt, thread_prompt)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save prompts")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in save_prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompts")
async def get_prompts(user_id: int = Depends(get_current_user_id)):
    """Get prompts for a user."""
    try:
        db = SQLDatabase()
        prompts = db.get_prompts(user_id)
        if not prompts:
            raise HTTPException(status_code=404, detail="No prompts found")
        return prompts
    except Exception as e:
        logger.error(f"Error in get_prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-mbox-file")
async def process_mbox_file(
    file: UploadFile = File(...),
    request: MboxUploadRequest = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    """Process an uploaded .mbox file and generate concepts."""
    try:
        if not file.filename.endswith('.mbox'):
            raise HTTPException(status_code=400, detail="File must be a .mbox file")

        logger.info(f"Processing mbox file: {file.filename}")
        db = SQLDatabase()
        
        # Verify user exists and get their collection ID
        user = db.get_user(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chroma_collection_id = user["chroma_collection_id"]
        
        # Initialize vector DB and concept extractor
        vector_db = ChromaDatabase(
            embedding_model_name=request.embedding_model_name,
            collection_name=chroma_collection_id
        )
        concept_extractor = ConceptExtractor(
            sql_db=db,
            vector_db=vector_db,
            model=request.model_name,
        )

        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mbox') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Process the mbox file
            email_loader = EmailLoader()
            processed_emails = 0
            for formatted_message in email_loader.process_mbox_file(temp_file.name):
                if "error" in formatted_message:
                    logger.error(f"Error in message: {formatted_message['error']}")
                    continue
                    
                db.store_email(formatted_message, user_id)
                processed_emails += 1

        # Clean up the temporary file
        os.unlink(temp_file.name)

        # Process concepts from unprocessed emails
        emails = db.get_unprocessed_emails(user_id)
        processed_concepts = 0
        for email in emails:
            success, stored_count = concept_extractor.process_email_concepts(
                email, 
                request.similarity_threshold, 
                user_id,
                chroma_collection_id
            )
            if success:
                processed_concepts += stored_count

        return {
            "status": "success",
            "processed_emails": processed_emails,
            "processed_concepts": processed_concepts
        }

    except Exception as e:
        logger.error(f"Error in process_mbox_file: {str(e)}", exc_info=True)
        error_detail = {
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_detail)