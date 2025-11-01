"""
API Routers for Conversation-related endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional

from ..schemas import (
    TutorConversationRequest,
    TutorConversationResponse,
    RomanConversationRequest,
    RomanConversationResponse,
    ScenariosListResponse,
    StruggleDetectionResponse,
)
from ..auth import get_current_user, validate_learner_exists
from ..conversations import (
    start_tutor_conversation,
    continue_tutor_conversation,
    start_roman_conversation,
    continue_roman_conversation,
    load_scenarios,
    save_conversation,
    load_conversation,
    detect_struggle_patterns,
    get_recent_conversations,
    get_conversation_stats,
    count_conversation_toward_progress
)
from ..tools import load_learner_model
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/conversations/tutor", response_model=TutorConversationResponse)
async def tutor_conversation(request: TutorConversationRequest, learner_id: str = Depends(validate_learner_exists)):
    """
    Start or continue a conversation with the Latin tutor.
    """
    try:
        if not request.conversation_id:
            conversation = start_tutor_conversation(learner_id=request.learner_id, concept_id=request.concept_id)
            save_conversation(conversation)
            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": conversation.messages[-1].content,
                "conversation_history": [m.to_dict() for m in conversation.messages]
            }
        else:
            conversation = load_conversation(conversation_id=request.conversation_id, learner_id=request.learner_id)
            if not conversation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            if not request.message:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message required to continue conversation")
            tutor_response = continue_tutor_conversation(conversation, request.message)
            save_conversation(conversation)
            if conversation.get_message_count() >= 6:
                count_conversation_toward_progress(conversation)
            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": tutor_response,
                "conversation_history": [m.to_dict() for m in conversation.messages]
            }
    except Exception as e:
        logger.error(f"Error in tutor conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process tutor conversation: {str(e)}")


@router.post("/conversations/roman", response_model=RomanConversationResponse)
async def roman_conversation(request: RomanConversationRequest, learner_id: str = Depends(validate_learner_exists)):
    """
    Start or continue a conversation with a Roman character.
    """
    try:
        if not request.conversation_id:
            learner_model = load_learner_model(request.learner_id)
            concept_data = learner_model.get("concepts", {}).get(request.concept_id, {})
            recent_assessments = concept_data.get("assessments", [])[-5:]
            learner_performance = None
            if recent_assessments:
                recent_scores = [a.get("score", 0.7) for a in recent_assessments]
                recent_average = sum(recent_scores) / len(recent_scores)
                learner_performance = {"recent_average_score": recent_average}
            conversation = start_roman_conversation(
                learner_id=request.learner_id,
                concept_id=request.concept_id,
                scenario_id=request.scenario_id,
                learner_performance=learner_performance
            )
            save_conversation(conversation)
            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": conversation.messages[-1].content,
                "conversation_history": [m.to_dict() for m in conversation.messages],
                "scenario": conversation.scenario
            }
        else:
            # ... (logic for continuing conversation)
            pass
    except Exception as e:
        logger.error(f"Error in Roman conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process Roman conversation: {str(e)}")


@router.get("/conversations/scenarios/{concept_id}", response_model=ScenariosListResponse)
async def get_scenarios(concept_id: str):
    """
    Get available Roman character scenarios for a concept.
    """
    try:
        scenarios = load_scenarios(concept_id)
        if not scenarios:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No scenarios found for concept: {concept_id}")
        return {"concept_id": concept_id, "scenarios": scenarios}
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get scenarios: {str(e)}")


@router.get("/conversations/detect-struggle/{learner_id}/{concept_id}", response_model=StruggleDetectionResponse)
async def detect_struggle(concept_id: str, learner_id: str = Depends(validate_learner_exists)):
    """
    Detect if a learner is struggling based on conversation patterns.
    """
    try:
        result = detect_struggle_patterns(learner_id, concept_id)
        return {
            "is_struggling": result.get("is_struggling", False),
            "topics": result.get("topics", []),
            "recommendation": result.get("recommendation"),
            "intervention": result.get("intervention")
        }
    except Exception as e:
        logger.error(f"Error detecting struggle: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to detect struggle: {str(e)}")


@router.get("/conversations/stats/{learner_id}")
async def get_stats(learner_id: str = Depends(validate_learner_exists), concept_id: Optional[str] = None):
    """
    Get conversation statistics for a learner.
    """
    try:
        stats = get_conversation_stats(learner_id, concept_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get conversation stats: {str(e)}")
