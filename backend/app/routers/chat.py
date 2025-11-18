from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional, List, Dict, Any
import logging

from .. import config
from ..schemas import (
    ChatRequest,
    ChatResponse,
    TutorConversationRequest,
    TutorConversationResponse,
    RomanConversationRequest,
    RomanConversationResponse,
    ConversationHistoryRequest,
    StruggleDetectionResponse,
    ScenariosListResponse
)
from ..agent import chat
from ..tutor_agent import start_tutor_conversation, continue_tutor_conversation
from ..roman_agent import start_roman_conversation, continue_roman_conversation, load_scenarios
from ..conversations import (
    get_recent_conversations,
    detect_struggle_patterns
)

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)
limiter = None # Will be injected from main app

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request_obj: Request, request: ChatRequest):
    """
    Send a message to the AI tutor and get a response.

    Handles conversation with the adaptive learning agent, including
    tool use for resource loading and progress tracking.
    """
    try:
        result = chat(
            learner_id=request.learner_id,
            user_message=request.message,
            conversation_history=request.conversation_history
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Chat failed")
            )

        return {
            "success": True,
            "message": result["message"],
            "conversation_history": result["conversation_history"]
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {request.learner_id}"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@router.post("/tutor/conversation", response_model=TutorConversationResponse)
async def tutor_conversation(request: TutorConversationRequest):
    """
    Start or continue a conversation with the Socratic tutor.
    """
    try:
        if request.conversation_id:
            # Continue existing conversation
            result = continue_tutor_conversation(
                conversation_id=request.conversation_id,
                user_message=request.message,
                learner_id=request.learner_id
            )
        else:
            # Start new conversation
            result = start_tutor_conversation(
                learner_id=request.learner_id,
                concept_id=request.concept_id,
                initial_message=request.message
            )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Conversation failed")
            )

        return result

    except Exception as e:
        logger.error(f"Error in tutor conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation failed: {str(e)}"
        )

@router.post("/roman/conversation", response_model=RomanConversationResponse)
async def roman_conversation(request: RomanConversationRequest):
    """
    Start or continue a conversation with a Roman character.
    """
    try:
        if request.conversation_id:
            # Continue existing conversation
            result = continue_roman_conversation(
                conversation_id=request.conversation_id,
                user_message=request.message,
                learner_id=request.learner_id
            )
        else:
            # Start new conversation
            result = start_roman_conversation(
                learner_id=request.learner_id,
                concept_id=request.concept_id,
                scenario_id=request.scenario_id,
                initial_message=request.message
            )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Conversation failed")
            )

        return result

    except Exception as e:
        logger.error(f"Error in Roman conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation failed: {str(e)}"
        )

@router.get("/roman/scenarios/{concept_id}", response_model=ScenariosListResponse)
async def list_scenarios(concept_id: str):
    """
    List available Roman character scenarios for a concept.
    """
    try:
        scenarios = load_scenarios(concept_id)
        return {
            "concept_id": concept_id,
            "scenarios": scenarios
        }
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        return {
            "concept_id": concept_id,
            "scenarios": []
        }

@router.post("/history", response_model=List[Dict[str, Any]])
async def get_history(request: ConversationHistoryRequest):
    """
    Get conversation history for a learner.
    """
    try:
        conversations = get_recent_conversations(
            learner_id=request.learner_id,
            limit=request.limit,
            concept_id=request.concept_id,
            conversation_type=request.conversation_type
        )
        return conversations
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )

@router.get("/struggle/{learner_id}", response_model=StruggleDetectionResponse)
async def check_struggle(learner_id: str):
    """
    Check if the learner is struggling with recent concepts.
    """
    try:
        struggle_data = detect_struggle_patterns(learner_id)
        return struggle_data
    except Exception as e:
        logger.error(f"Error checking struggle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check struggle: {str(e)}"
        )
