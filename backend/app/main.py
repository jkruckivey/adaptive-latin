"""
FastAPI Application for Latin Adaptive Learning System

Main application with REST API endpoints for the adaptive learning tutor.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .config import config
from .agent import chat, generate_content
from .tools import (
    create_learner_model,
    load_learner_model,
    load_concept_metadata,
    calculate_mastery,
    list_all_concepts
)
from .confidence import calculate_overall_calibration
from .spaced_repetition import get_due_reviews, get_review_stats
from .conversations import (
    save_conversation,
    load_conversation,
    get_recent_conversations,
    detect_struggle_patterns,
    count_conversation_toward_progress,
    get_conversation_stats
)
from .tutor_agent import start_tutor_conversation, continue_tutor_conversation
from .roman_agent import start_roman_conversation, continue_roman_conversation, load_scenarios

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Latin Adaptive Learning API",
    description="Backend API for AI-powered adaptive Latin grammar learning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models for Request/Response Validation
# ============================================================================

class StartRequest(BaseModel):
    """Request to start a new learner session."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    learner_name: Optional[str] = Field(None, description="Learner's name")
    profile: Optional[Dict[str, Any]] = Field(None, description="Learner profile from onboarding")


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    message: str = Field(..., description="User's message to the tutor")
    conversation_history: Optional[List[dict]] = Field(None, description="Previous conversation messages")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    success: bool
    message: str
    conversation_history: List[dict]
    error: Optional[str] = None


class ProgressResponse(BaseModel):
    """Response with learner progress information."""
    learner_id: str
    current_concept: str
    concepts_completed: int
    concepts_in_progress: int
    total_assessments: int
    average_calibration_accuracy: float
    concept_details: dict
    overall_calibration: Optional[dict] = None


class ConceptResponse(BaseModel):
    """Response with concept information."""
    concept_id: str
    title: str
    difficulty: int
    prerequisites: List[str]
    learning_objectives: List[str]
    estimated_mastery_time: str
    vocabulary: List[dict]


class MasteryResponse(BaseModel):
    """Response with mastery information."""
    concept_id: str
    mastery_achieved: bool
    mastery_score: float
    assessments_completed: int
    recommendation: str
    reason: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str


class SubmitResponseRequest(BaseModel):
    """Request to submit and evaluate a learner response."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    question_type: str = Field(..., description="Type of question (multiple-choice, fill-blank, dialogue)")
    user_answer: Any = Field(..., description="Learner's answer (index for MC, string for others)")
    correct_answer: Any = Field(..., description="Correct answer")
    confidence: Optional[int] = Field(None, ge=1, le=4, description="Confidence level (1-4 stars), optional for adaptive frequency")
    current_concept: str = Field(..., description="Concept being tested")
    question_text: Optional[str] = Field(None, description="The question text")
    scenario_text: Optional[str] = Field(None, description="The scenario text (if any)")
    options: Optional[List[str]] = Field(None, description="List of answer options for multiple-choice questions")


class EvaluationResponse(BaseModel):
    """Response after evaluating a learner's answer."""
    is_correct: bool
    confidence: int
    calibration_type: str  # "calibrated", "overconfident", "underconfident"
    feedback_message: str
    next_content: dict  # The next piece of content to show
    debug_context: Optional[dict] = None  # Debug info showing what was sent to AI


class TutorConversationRequest(BaseModel):
    """Request to start or continue a tutor conversation."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")


class TutorConversationResponse(BaseModel):
    """Response from tutor conversation endpoint."""
    success: bool
    conversation_id: str
    message: str  # The tutor's response
    conversation_history: List[dict]
    error: Optional[str] = None


class ConversationHistoryRequest(BaseModel):
    """Request to get conversation history."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: Optional[str] = Field(None, description="Filter by concept (optional)")
    conversation_type: Optional[str] = Field(None, description="Filter by type: 'tutor' or 'roman' (optional)")
    hours: int = Field(24, description="Get conversations from last N hours")
    limit: int = Field(10, description="Maximum number of conversations to return")


class StruggleDetectionResponse(BaseModel):
    """Response from struggle detection endpoint."""
    is_struggling: bool
    topics: List[str] = []
    recommendation: Optional[str] = None
    intervention: Optional[str] = None


class RomanConversationRequest(BaseModel):
    """Request to start or continue a Roman character conversation."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")
    scenario_id: Optional[str] = Field(None, description="Specific scenario to use (optional)")


class RomanConversationResponse(BaseModel):
    """Response from Roman conversation endpoint."""
    success: bool
    conversation_id: str
    message: str  # The Roman character's response
    conversation_history: List[dict]
    scenario: dict  # Scenario information (character name, setting, etc.)
    error: Optional[str] = None


class ScenariosListResponse(BaseModel):
    """List of available scenarios for a concept."""
    concept_id: str
    scenarios: List[dict]


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Validate configuration and ensure directories exist on startup."""
    try:
        logger.info("Starting Latin Adaptive Learning API...")
        config.validate()
        config.ensure_directories()
        logger.info("Configuration validated successfully")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"Resource bank: {config.RESOURCE_BANK_DIR}")
        logger.info(f"Learner models: {config.LEARNER_MODELS_DIR}")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down Latin Adaptive Learning API...")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns basic application status and version information.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": config.ENVIRONMENT
    }


@app.post("/start", status_code=status.HTTP_201_CREATED)
async def start_learner(request: StartRequest):
    """
    Initialize a new learner.

    Creates a new learner model and returns the initial state.
    """
    try:
        learner_model = create_learner_model(
            request.learner_id,
            learner_name=request.learner_name,
            profile=request.profile
        )
        logger.info(f"Started new learner: {request.learner_id}")

        return {
            "success": True,
            "learner_id": request.learner_id,
            "current_concept": learner_model["current_concept"],
            "message": "Learner initialized successfully. Ready to begin learning!"
        }

    except ValueError as e:
        # Learner already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting learner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize learner: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
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


@app.get("/progress/{learner_id}", response_model=ProgressResponse)
async def get_progress(learner_id: str):
    """
    Get learner's progress information.

    Returns detailed progress including current concept, mastery scores,
    and calibration metrics.
    """
    try:
        model = load_learner_model(learner_id)

        # Collect all confidence history
        all_confidence = []
        for concept_data in model["concepts"].values():
            all_confidence.extend(concept_data.get("confidence_history", []))

        # Calculate overall calibration metrics
        overall_calibration = None
        if all_confidence:
            overall_calibration = calculate_overall_calibration(all_confidence)

        return {
            "learner_id": learner_id,
            "current_concept": model["current_concept"],
            "concepts_completed": model["overall_progress"]["concepts_completed"],
            "concepts_in_progress": model["overall_progress"]["concepts_in_progress"],
            "total_assessments": model["overall_progress"]["total_assessments"],
            "average_calibration_accuracy": model["overall_progress"].get("average_calibration_accuracy", 0.0),
            "concept_details": model["concepts"],
            "overall_calibration": overall_calibration
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@app.get("/concept/{concept_id}", response_model=ConceptResponse)
async def get_concept_info(concept_id: str):
    """
    Get information about a specific concept.

    Returns metadata including title, objectives, vocabulary, etc.
    """
    try:
        metadata = load_concept_metadata(concept_id)

        return {
            "concept_id": metadata["id"],
            "title": metadata["title"],
            "difficulty": metadata["difficulty"],
            "prerequisites": metadata["prerequisites"],
            "learning_objectives": metadata["learning_objectives"],
            "estimated_mastery_time": metadata["estimated_mastery_time"],
            "vocabulary": metadata.get("vocabulary", [])
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept not found: {concept_id}"
        )
    except Exception as e:
        logger.error(f"Error getting concept info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get concept info: {str(e)}"
        )


@app.get("/mastery/{learner_id}/{concept_id}", response_model=MasteryResponse)
async def get_mastery(learner_id: str, concept_id: str):
    """
    Get mastery information for a specific concept.

    Returns mastery score, recommendation, and assessment details.
    """
    try:
        mastery_info = calculate_mastery(learner_id, concept_id)

        return mastery_info

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner or concept not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating mastery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate mastery: {str(e)}"
        )


@app.get("/concepts")
async def list_concepts():
    """
    List all available concepts.

    Returns a list of all concept IDs in the resource bank.
    """
    try:
        concepts = list_all_concepts()
        return {
            "success": True,
            "concepts": concepts,
            "total": len(concepts)
        }

    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list concepts: {str(e)}"
        )


@app.get("/learner/{learner_id}")
async def get_learner_model(learner_id: str):
    """
    Get the complete learner model including profile data.

    This endpoint is useful for debugging and testing to see
    what profile information was collected during onboarding.
    """
    try:
        model = load_learner_model(learner_id)
        return {
            "success": True,
            "learner_model": model
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except Exception as e:
        logger.error(f"Error getting learner model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learner model: {str(e)}"
        )


@app.post("/submit-response", response_model=EvaluationResponse)
async def submit_response(request: SubmitResponseRequest):
    """
    Evaluate a learner's response and generate adaptive next content.

    Uses confidence × correctness matrix to determine what content to show:
    - Correct + High Confidence → Next diagnostic (no lesson)
    - Correct + Low Confidence → Brief reinforcement
    - Incorrect + High Confidence → Full lesson + calibration feedback
    - Incorrect + Low Confidence → Supportive lesson
    """
    try:
        # Evaluate correctness
        is_correct = False
        if request.question_type == "multiple-choice":
            is_correct = request.user_answer == request.correct_answer
        elif request.question_type == "fill-blank":
            is_correct = request.user_answer.lower().strip() == request.correct_answer.lower().strip()
        # For dialogue, we'd need AI evaluation (future enhancement)

        # Determine calibration type and next content stage
        if request.confidence is None:
            # No confidence rating - skip calibration, decide based on correctness only
            calibration_type = None
            if is_correct:
                stage = "practice"
                remediation_type = None
            else:
                stage = "remediate"
                remediation_type = "supportive"
        else:
            # Has confidence rating - use confidence × correctness matrix
            high_confidence = request.confidence >= 3

            if is_correct and high_confidence:
                calibration_type = "calibrated"
                stage = "practice"
                remediation_type = None
            elif is_correct and not high_confidence:
                calibration_type = "underconfident"
                stage = "reinforce"
                remediation_type = "brief"
            elif not is_correct and high_confidence:
                calibration_type = "overconfident"
                stage = "remediate"
                remediation_type = "full_calibration"
            else:  # incorrect and low confidence
                calibration_type = "calibrated_low"
                stage = "remediate"
                remediation_type = "supportive"

        # Build question context for specific feedback
        question_context = None
        if (stage in ["remediate", "reinforce"]) and (request.question_text or request.scenario_text):
            # We're providing feedback on a specific question - pass the details to AI
            question_context = {
                "scenario": request.scenario_text or "",
                "question": request.question_text or "",
                "user_answer": request.user_answer,
                "correct_answer": request.correct_answer,
                "options": request.options or []
            }
            logger.info(f"Passing question context to AI for {stage} feedback")

        # Generate next content using the AI
        result = generate_content(
            request.learner_id,
            stage,
            correctness=is_correct,
            confidence=request.confidence,
            remediation_type=remediation_type,
            question_context=question_context
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate next content"
            )

        # Save question to history to avoid repetition
        if request.question_text or request.scenario_text:
            try:
                from .tools import load_learner_model, save_learner_model
                from datetime import datetime

                learner_model = load_learner_model(request.learner_id)

                # Add current question to history
                question_entry = {
                    "scenario": request.scenario_text or "",
                    "question": request.question_text or "",
                    "user_answer": request.user_answer,
                    "correct_answer": request.correct_answer,
                    "timestamp": datetime.now().isoformat(),
                    "was_correct": is_correct,
                    "confidence": request.confidence
                }

                # Initialize question_history if it doesn't exist (for older learner models)
                if "question_history" not in learner_model:
                    learner_model["question_history"] = []

                learner_model["question_history"].append(question_entry)

                # Keep only last 10 questions to avoid unbounded growth
                learner_model["question_history"] = learner_model["question_history"][-10:]

                # Update timestamp
                learner_model["updated_at"] = datetime.now().isoformat()

                save_learner_model(request.learner_id, learner_model)
                logger.info(f"Saved question to history for {request.learner_id}")
            except Exception as e:
                logger.warning(f"Failed to save question history: {e}")
                # Don't fail the request if history saving fails

        # Create feedback message
        feedback_messages = {
            "calibrated": "Well done! You knew it and got it right.",
            "underconfident": "You got it right! You know more than you think.",
            "overconfident": "Not quite - let's clarify this concept.",
            "calibrated_low": "You weren't sure, and this is tricky. Let's work through it."
        }

        return {
            "is_correct": is_correct,
            "confidence": request.confidence,
            "calibration_type": calibration_type,
            "feedback_message": feedback_messages[calibration_type],
            "next_content": result["content"],
            "debug_context": {
                "stage": stage,
                "remediation_type": remediation_type,
                "question_context_sent_to_ai": question_context
            }
        }

    except Exception as e:
        logger.error(f"Error evaluating response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate response: {str(e)}"
        )


@app.post("/generate-content")
async def generate_content_endpoint(learner_id: str, stage: str = "start"):
    """
    Generate personalized learning content using AI.

    Uses learner profile to create customized lessons, examples, and assessments.

    Args:
        learner_id: Unique identifier for the learner
        stage: Learning stage ("start", "practice", "assess")

    Returns:
        Generated content object (lesson, example-set, multiple-choice, etc.)
    """
    try:
        result = generate_content(learner_id, stage)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Content generation failed")
            )

        return result

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


# ============================================================================
# Spaced Repetition / Review Endpoints
# ============================================================================

@app.get("/reviews/{learner_id}")
async def get_due_concepts(learner_id: str, include_upcoming: int = 0):
    """
    Get concepts that are due for spaced repetition review.

    Args:
        learner_id: The learner's unique identifier
        include_upcoming: Include concepts due within N days (default 0 = today only)

    Returns:
        List of concepts due for review, sorted by priority
    """
    try:
        model = load_learner_model(learner_id)
        due_concepts = get_due_reviews(model, include_upcoming=include_upcoming)

        return {
            "success": True,
            "learner_id": learner_id,
            "due_count": len(due_concepts),
            "include_upcoming_days": include_upcoming,
            "due_concepts": due_concepts
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except Exception as e:
        logger.error(f"Error getting due reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get due reviews: {str(e)}"
        )


@app.get("/review-stats/{learner_id}")
async def get_review_statistics(learner_id: str):
    """
    Get overall statistics about spaced repetition progress.

    Args:
        learner_id: The learner's unique identifier

    Returns:
        Statistics including total reviews, concepts due, etc.
    """
    try:
        model = load_learner_model(learner_id)
        stats = get_review_stats(model)

        return {
            "success": True,
            "learner_id": learner_id,
            **stats
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except Exception as e:
        logger.error(f"Error getting review stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review stats: {str(e)}"
        )


# ============================================================================
# Conversation Endpoints ("Talk to Tutor" and "Talk to Roman")
# ============================================================================

@app.post("/conversations/tutor", response_model=TutorConversationResponse)
async def tutor_conversation(request: TutorConversationRequest):
    """
    Start or continue a conversation with the Latin tutor.

    The tutor provides Socratic guidance, conceptual explanations, and
    encouragement. It has guardrails to prevent giving direct answers to
    assessment questions and stays focused on the current concept.

    Args:
        request: Contains learner_id, concept_id, optional message and conversation_id

    Returns:
        Conversation response with tutor's message and full history
    """
    try:
        # Start new conversation
        if not request.conversation_id:
            conversation = start_tutor_conversation(
                learner_id=request.learner_id,
                concept_id=request.concept_id
            )

            # Save conversation
            save_conversation(conversation)

            # Return initial greeting
            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": conversation.messages[-1].content,  # Last message is tutor's greeting
                "conversation_history": [m.to_dict() for m in conversation.messages]
            }

        # Continue existing conversation
        else:
            conversation = load_conversation(
                conversation_id=request.conversation_id,
                learner_id=request.learner_id
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation not found: {request.conversation_id}"
                )

            if not request.message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message required to continue conversation"
                )

            # Generate tutor response
            tutor_response = continue_tutor_conversation(conversation, request.message)

            # Save updated conversation
            save_conversation(conversation)

            # Check if conversation is long enough to count toward progress
            if conversation.get_message_count() >= 6:
                try:
                    count_conversation_toward_progress(conversation)
                except Exception as e:
                    logger.warning(f"Failed to count conversation toward progress: {e}")

            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": tutor_response,
                "conversation_history": [m.to_dict() for m in conversation.messages]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in tutor conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process tutor conversation: {str(e)}"
        )


@app.post("/conversations/roman", response_model=RomanConversationResponse)
async def roman_conversation(request: RomanConversationRequest):
    """
    Start or continue a conversation with a Roman character.

    Roman characters are everyday people (merchants, students, poets) who
    demonstrate Latin grammar in natural contexts. Students practice speaking
    Latin in immersive scenarios.

    Args:
        request: Contains learner_id, concept_id, optional message, conversation_id, and scenario_id

    Returns:
        Conversation response with Roman character's message and scenario info
    """
    try:
        # Start new conversation
        if not request.conversation_id:
            # Get learner performance for scenario selection
            try:
                learner_model = load_learner_model(request.learner_id)
                concept_data = learner_model.get("concepts", {}).get(request.concept_id, {})
                recent_assessments = concept_data.get("assessments", [])[-5:]

                if recent_assessments:
                    recent_scores = [a.get("score", 0.7) for a in recent_assessments]
                    recent_average = sum(recent_scores) / len(recent_scores)
                    learner_performance = {"recent_average_score": recent_average}
                else:
                    learner_performance = None
            except:
                learner_performance = None

            # Start conversation with selected scenario
            conversation = start_roman_conversation(
                learner_id=request.learner_id,
                concept_id=request.concept_id,
                scenario_id=request.scenario_id,
                learner_performance=learner_performance
            )

            # Save conversation
            save_conversation(conversation)

            # Return initial greeting
            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": conversation.messages[-1].content,  # Last message is character's greeting
                "conversation_history": [m.to_dict() for m in conversation.messages],
                "scenario": conversation.scenario
            }

        # Continue existing conversation
        else:
            conversation = load_conversation(
                conversation_id=request.conversation_id,
                learner_id=request.learner_id
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation not found: {request.conversation_id}"
                )

            if not request.message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message required to continue conversation"
                )

            # Generate Roman character response
            roman_response = continue_roman_conversation(conversation, request.message)

            # Save updated conversation
            save_conversation(conversation)

            # Check if conversation is long enough to count toward progress
            if conversation.get_message_count() >= 6:
                try:
                    count_conversation_toward_progress(conversation)
                except Exception as e:
                    logger.warning(f"Failed to count conversation toward progress: {e}")

            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "message": roman_response,
                "conversation_history": [m.to_dict() for m in conversation.messages],
                "scenario": conversation.scenario
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Roman conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Roman conversation: {str(e)}"
        )


@app.get("/conversations/scenarios/{concept_id}", response_model=ScenariosListResponse)
async def get_scenarios(concept_id: str):
    """
    Get available Roman character scenarios for a concept.

    Useful for displaying scenario options to the learner before starting
    a Roman conversation.

    Args:
        concept_id: The concept to get scenarios for

    Returns:
        List of available scenarios with character info
    """
    try:
        scenarios = load_scenarios(concept_id)

        if not scenarios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No scenarios found for concept: {concept_id}"
            )

        return {
            "concept_id": concept_id,
            "scenarios": scenarios
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenarios: {str(e)}"
        )


@app.post("/conversations/history")
async def get_conversation_history(request: ConversationHistoryRequest):
    """
    Get recent conversation history for a learner.

    Useful for displaying past conversations or analyzing learner engagement.

    Args:
        request: Contains learner_id and optional filters

    Returns:
        List of recent conversations
    """
    try:
        conversations = get_recent_conversations(
            learner_id=request.learner_id,
            concept_id=request.concept_id,
            conversation_type=request.conversation_type,
            hours=request.hours,
            limit=request.limit
        )

        return {
            "success": True,
            "count": len(conversations),
            "conversations": [c.to_dict() for c in conversations]
        }

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@app.get("/conversations/detect-struggle/{learner_id}/{concept_id}", response_model=StruggleDetectionResponse)
async def detect_struggle(learner_id: str, concept_id: str):
    """
    Detect if a learner is struggling based on conversation patterns.

    Analyzes recent tutor conversations to identify:
    - Repeated questions about the same topic (3+ times in 1 hour)
    - Patterns indicating confusion or lack of understanding

    This can trigger interventions like extra practice or guided lessons.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Concept to analyze

    Returns:
        Struggle detection result with recommended interventions
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect struggle: {str(e)}"
        )


@app.get("/conversations/stats/{learner_id}")
async def get_stats(learner_id: str, concept_id: Optional[str] = None):
    """
    Get conversation statistics for a learner.

    Provides insights into:
    - Total conversations (tutor + Roman)
    - Average messages per conversation
    - Concepts discussed

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Optional filter by concept

    Returns:
        Conversation statistics
    """
    try:
        stats = get_conversation_stats(learner_id, concept_id)

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation stats: {str(e)}"
        )


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )


