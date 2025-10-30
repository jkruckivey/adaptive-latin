"""
FastAPI Application for Latin Adaptive Learning System

Main application with REST API endpoints for the adaptive learning tutor.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
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

# Request size limit middleware
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size to prevent memory exhaustion."""

    def __init__(self, app, max_size: int = 1024 * 1024):  # Default 1MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large. Maximum size is {self.max_size} bytes."
                }
            )
        return await call_next(request)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Latin Adaptive Learning API",
    description="Backend API for AI-powered adaptive Latin grammar learning",
    version="1.0.0"
)

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add validation exception handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with details for debugging."""
    logger.error(f"Validation error on {request.url.path}:")
    for error in exc.errors():
        logger.error(f"  Field: {error['loc']}, Error: {error['msg']}, Input: {error.get('input', 'N/A')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# Add request size limit middleware (1MB max)
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)

# Configure CORS - restrict to only necessary methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],  # Allow GET, POST, PUT for updating resources
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Only allow needed headers
)


# ============================================================================
# Dependency Functions for Validation
# ============================================================================

async def validate_learner_exists(learner_id: str) -> str:
    """
    Validate that a learner exists before allowing operations.

    This provides basic protection against unauthorized access to learner data.
    For production, consider implementing JWT-based authentication.

    Args:
        learner_id: The learner ID to validate

    Returns:
        learner_id if valid

    Raises:
        HTTPException: If learner doesn't exist
    """
    try:
        from .tools import load_learner_model
        load_learner_model(learner_id)  # Will raise FileNotFoundError if not exists
        return learner_id
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}. Please start a new session."
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
    confidence: Optional[int] = None  # Optional when confidence slider is disabled
    calibration_type: Optional[str] = None  # Optional when no confidence rating
    feedback_message: str
    mastery_score: float  # Add mastery tracking
    mastery_threshold: float
    assessments_count: int
    concept_completed: bool
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


class CourseMetadata(BaseModel):
    """Course metadata structure."""
    course_id: str
    title: str
    domain: str
    taxonomy: Optional[str] = "blooms"
    course_learning_outcomes: List[str] = []
    # Keep these for backward compatibility with old courses
    description: Optional[str] = None
    target_audience: Optional[str] = None
    created_at: str
    updated_at: str
    concepts: List[dict] = []


class CreateCourseRequest(BaseModel):
    """Request to create a new course."""
    course_id: str = Field(..., description="Unique course identifier (e.g., 'spanish-101')")
    title: str = Field(..., description="Course title")
    domain: str = Field(..., description="Subject area")
    taxonomy: str = Field(default="blooms", description="Learning outcome framework (blooms, finks, or both)")
    course_learning_outcomes: List[str] = Field(default=[], description="Course-level learning outcomes (CLOs)")
    # Keep these for backward compatibility with old courses
    description: Optional[str] = Field(default=None, description="Course description (deprecated)")
    target_audience: Optional[str] = Field(default=None, description="Target audience (deprecated)")
    concepts: List[dict] = Field(default=[], description="Course concepts/modules")


class CoursesListResponse(BaseModel):
    """Response with list of available courses."""
    courses: List[dict]
    total: int


class AddSourceRequest(BaseModel):
    """Request to add an external source to a course or concept."""
    url: str = Field(..., description="Source URL")
    source_type: Optional[str] = Field(None, description="Source type (auto-detected if not provided)")
    title: Optional[str] = Field(None, description="Optional custom title")
    description: Optional[str] = Field(None, description="Optional custom description")
    requirement_level: Optional[str] = Field(default="optional", description="Requirement level: optional, recommended, or required")
    verification_method: Optional[str] = Field(default="none", description="Verification method: none, self-attestation, comprehension-quiz, or discussion-prompt")
    verification_data: Optional[dict] = Field(default=None, description="Verification data (quiz questions, discussion prompts, etc.)")


class SourceResponse(BaseModel):
    """Response with source metadata."""
    source_id: str
    type: str
    url: str
    title: str
    description: str
    metadata: dict
    added_at: str
    status: str
    error_message: Optional[str] = None


class SourceContentResponse(BaseModel):
    """Response with full source content."""
    success: bool
    content: Optional[str] = None
    content_type: str
    length: Optional[int] = None
    error: Optional[str] = None


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

        # Initialize content cache database
        try:
            from .content_cache import init_database
            init_database()
            logger.info("✅ Content cache database initialized")
        except Exception as e:
            logger.warning(f"⚠️  Content cache initialization failed: {e}")
            logger.warning("⚠️  Content caching will not be available")

        # Log directory status for debugging
        logger.info(f"Learner models directory: {config.LEARNER_MODELS_DIR}")
        logger.info(f"Directory exists: {config.LEARNER_MODELS_DIR.exists()}")
        logger.info(f"Directory writable: {os.access(config.LEARNER_MODELS_DIR, os.W_OK)}")

        # Test write permissions
        test_file = config.LEARNER_MODELS_DIR / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            logger.info("✅ Learner models directory is writable")
        except Exception as e:
            logger.error(f"❌ Cannot write to learner models directory: {e}")
            logger.warning("⚠️  Learner data will not persist! Consider using a database or persistent storage.")

        # Validate CORS configuration for production safety
        if "*" in config.CORS_ORIGINS:
            if config.ENVIRONMENT == "production":
                raise ValueError("CORS wildcard (*) is not allowed in production. Please specify explicit origins.")
            else:
                logger.warning("⚠️  CORS wildcard (*) detected - acceptable for development but NOT for production!")

        # Production storage warning
        if config.ENVIRONMENT == "production":
            logger.warning("⚠️  PRODUCTION MODE: Using local filesystem for learner data.")
            logger.warning("⚠️  Data will be lost on container restart. Consider using a database for persistence.")

        logger.info("Configuration validated successfully")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"CORS Origins: {', '.join(config.CORS_ORIGINS)}")
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
@limiter.limit("10/minute")  # Limit learner creation to prevent spam
async def start_learner(request: Request, body: StartRequest):
    """
    Initialize a new learner.

    Creates a new learner model and returns the initial state.
    """
    try:
        logger.info(f"📝 Creating new learner: {body.learner_id}")
        logger.info(f"   Name: {body.learner_name}")
        logger.info(f"   Has profile: {body.profile is not None}")

        learner_model = create_learner_model(
            body.learner_id,
            learner_name=body.learner_name,
            profile=body.profile
        )

        # Verify the file was actually created
        learner_file = config.get_learner_file(body.learner_id)
        if learner_file.exists():
            logger.info(f"✅ Learner model file created: {learner_file}")
            logger.info(f"   File size: {learner_file.stat().st_size} bytes")
        else:
            logger.error(f"❌ Learner model file NOT found after creation: {learner_file}")

        logger.info(f"🎉 Successfully started learner: {body.learner_id}")

        return {
            "success": True,
            "learner_id": body.learner_id,
            "current_concept": learner_model["current_concept"],
            "message": "Learner initialized successfully. Ready to begin learning!"
        }

    except ValueError as e:
        # Learner already exists
        logger.warning(f"Learner {body.learner_id} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error starting learner {body.learner_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize learner: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Reasonable limit for chat interactions
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


@app.put("/learner/{learner_id}/learning-style")
async def update_learning_style(learner_id: str, body: dict):
    """
    Update the learner's learning style preference.

    This allows learners to change their preferred content format
    (narrative, varied, adaptive) after experiencing the initial choice.
    """
    try:
        from .tools import load_learner_model, save_learner_model

        # Validate learning style
        valid_styles = ["narrative", "varied", "adaptive"]
        new_style = body.get("learningStyle")

        if not new_style:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="learningStyle field is required"
            )

        if new_style not in valid_styles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid learning style. Must be one of: {', '.join(valid_styles)}"
            )

        # Load learner model
        model = load_learner_model(learner_id)

        # Update learning style
        if "profile" not in model:
            model["profile"] = {}

        old_style = model["profile"].get("learningStyle", "unknown")
        model["profile"]["learningStyle"] = new_style

        # Save updated model
        save_learner_model(learner_id, model)

        logger.info(f"✅ Updated learning style for {learner_id}: {old_style} → {new_style}")

        return {
            "success": True,
            "message": f"Learning style updated to '{new_style}'",
            "previous_style": old_style,
            "new_style": new_style
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learning style: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update learning style: {str(e)}"
        )


@app.post("/submit-response", response_model=EvaluationResponse)
@limiter.limit("60/minute")  # Match content generation rate for smooth learning flow
async def submit_response(request: Request, body: SubmitResponseRequest):
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
        dialogue_feedback = None  # Initialize for use later
        dialogue_score = 0.0

        if body.question_type == "multiple-choice":
            is_correct = body.user_answer == body.correct_answer
        elif body.question_type == "fill-blank":
            # For fill-blank, correct_answer can be a string or list of acceptable answers
            user_answer_normalized = body.user_answer.lower().strip()

            if isinstance(body.correct_answer, list):
                # Multiple acceptable answers - check if user's answer matches any
                is_correct = any(
                    user_answer_normalized == acceptable.lower().strip()
                    for acceptable in body.correct_answer
                )
            else:
                # Single acceptable answer (backward compatibility)
                is_correct = user_answer_normalized == body.correct_answer.lower().strip()
        elif body.question_type == "dialogue":
            # Use AI to evaluate open-ended dialogue responses with rubric-based explanation
            from .agent import evaluate_dialogue_response

            evaluation = evaluate_dialogue_response(
                question=body.question_text,
                context=body.scenario_text or "",
                student_answer=body.user_answer,
                concept_id=body.current_concept
            )

            is_correct = evaluation.get("is_correct", False)
            dialogue_feedback = evaluation.get("feedback", "")
            dialogue_score = evaluation.get("score", 0.0)

        # Determine calibration type and next content stage
        if body.confidence is None:
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
            high_confidence = body.confidence >= 3

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

        # Dialogue questions disabled for now - keep using multiple-choice
        # Will re-enable when dialogue evaluation is fully implemented
        # (Commented out the dialogue transition logic)

        # Record assessment and check for concept completion
        from .tools import record_assessment_and_check_completion

        completion_result = record_assessment_and_check_completion(
            learner_id=body.learner_id,
            concept_id=body.current_concept,
            is_correct=is_correct,
            confidence=body.confidence,
            question_type=body.question_type
        )

        if completion_result["concept_completed"]:
            logger.info(
                f"🎉 Learner {body.learner_id} completed {body.current_concept}! "
                f"Total concepts: {completion_result['concepts_completed_total']}/7"
            )

        # Build question context for specific feedback
        question_context = None
        if (stage in ["remediate", "reinforce"]) and (body.question_text or body.scenario_text):
            # We're providing feedback on a specific question - pass the details to AI
            question_context = {
                "scenario": body.scenario_text or "",
                "question": body.question_text or "",
                "user_answer": body.user_answer,
                "correct_answer": body.correct_answer,
                "options": body.options or []
            }
            logger.info(f"Passing question context to AI for {stage} feedback")

        # Generate next content using the AI
        result = generate_content(
            body.learner_id,
            stage,
            correctness=is_correct,
            confidence=body.confidence,
            remediation_type=remediation_type,
            question_context=question_context
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate next content"
            )

        # Save question to history to avoid repetition
        if body.question_text or body.scenario_text:
            try:
                from .tools import load_learner_model, save_learner_model
                from datetime import datetime

                learner_model = load_learner_model(body.learner_id)

                # Add current question to history
                question_entry = {
                    "scenario": body.scenario_text or "",
                    "question": body.question_text or "",
                    "user_answer": body.user_answer,
                    "correct_answer": body.correct_answer,
                    "timestamp": datetime.now().isoformat(),
                    "was_correct": is_correct,
                    "confidence": body.confidence
                }

                # Initialize question_history if it doesn't exist (for older learner models)
                if "question_history" not in learner_model:
                    learner_model["question_history"] = []

                learner_model["question_history"].append(question_entry)

                # Keep only last 10 questions to avoid unbounded growth
                learner_model["question_history"] = learner_model["question_history"][-10:]

                # Update timestamp
                learner_model["updated_at"] = datetime.now().isoformat()

                save_learner_model(body.learner_id, learner_model)
                logger.info(f"Saved question to history for {body.learner_id}")
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

        # For dialogue questions, use the AI-generated rubric-based feedback
        if body.question_type == "dialogue":
            feedback_text = dialogue_feedback
        else:
            feedback_text = feedback_messages.get(calibration_type, "Thank you for your response.")

        # Build assessment-result content to show feedback
        # Convert correct answer to human-readable text
        correct_answer_display = body.correct_answer
        if body.question_type == "multiple-choice" and body.options and isinstance(body.correct_answer, int):
            # For multiple-choice, show the actual option text, not just the index
            if 0 <= body.correct_answer < len(body.options):
                correct_answer_display = body.options[body.correct_answer]

        # Language connection hint - placeholder for future feature
        language_connection = None

        # Create debug context
        debug_context = {
            "stage": stage,
            "remediation_type": remediation_type,
            "question_context_sent_to_ai": question_context,
            "mastery_score": completion_result.get("mastery_score", 0.0),
            "assessments_count": completion_result.get("assessments_count", 0)
        }

        logger.info(f"Debug context being sent: {debug_context}")

        assessment_result = {
            "type": "assessment-result",
            "score": 1.0 if is_correct else 0.0,
            "feedback": feedback_text,
            "correctAnswer": correct_answer_display if body.question_type != "dialogue" else None,
            "calibration": calibration_type,
            "languageConnection": language_connection,
            "_next_content": result["content"],  # Store for preloading, frontend will fetch on continue
            "debug_context": debug_context  # Add debug context to assessment result content
        }

        return {
            "is_correct": is_correct,
            "confidence": body.confidence,
            "calibration_type": calibration_type,
            "feedback_message": feedback_messages.get(calibration_type, "Thank you for your response."),
            "mastery_score": completion_result["mastery_score"],
            "mastery_threshold": config.MASTERY_THRESHOLD,
            "assessments_count": completion_result["assessments_count"],
            "concept_completed": completion_result["concept_completed"],
            "next_content": assessment_result,
            "debug_context": debug_context
        }

    except Exception as e:
        logger.error(f"Error evaluating response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate response: {str(e)}"
        )


@app.post("/generate-content")
@limiter.limit("60/minute")  # Allow frequent content generation during active learning
async def generate_content_endpoint(request: Request, learner_id: str, stage: str = "start"):
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

        # Add mastery data to debug context
        try:
            from .tools import load_learner_model
            learner_model = load_learner_model(learner_id)
            current_concept = learner_model.get("current_concept", "concept-001")

            mastery_score = 0.0
            assessments_count = 0

            if current_concept in learner_model.get("concepts", {}):
                concept_data = learner_model["concepts"][current_concept]
                mastery_score = concept_data.get("mastery_score", 0.0)
                assessments_count = len(concept_data.get("assessments", []))

            # Add debug context if it doesn't exist
            if "content" in result and isinstance(result["content"], dict):
                if "debug_context" not in result["content"]:
                    result["content"]["debug_context"] = {}

                result["content"]["debug_context"]["mastery_score"] = mastery_score
                result["content"]["debug_context"]["assessments_count"] = assessments_count
                result["content"]["debug_context"]["stage"] = stage
                result["content"]["debug_context"]["remediation_type"] = "none"
                result["content"]["debug_context"]["question_context_sent_to_ai"] = None
        except Exception as e:
            logger.warning(f"Could not add mastery data to debug context: {e}")

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
# Course Management Endpoints
# ============================================================================

@app.get("/courses", response_model=CoursesListResponse)
async def list_courses():
    """
    List all available courses (built-in and user-created).

    Returns:
        List of course metadata for all available courses
    """
    try:
        courses = []

        # Check for built-in courses in resource-bank
        if config.RESOURCE_BANK_DIR.exists():
            for item in config.RESOURCE_BANK_DIR.iterdir():
                if item.is_dir() and item.name not in ["user-courses"]:
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                                courses.append({
                                    "course_id": item.name,
                                    "title": metadata.get("title", item.name),
                                    "domain": metadata.get("domain", "Unknown"),
                                    "description": metadata.get("description", ""),
                                    "type": "built-in"
                                })
                        except Exception as e:
                            logger.warning(f"Could not load metadata for {item.name}: {e}")

        # Check for user-created courses
        if config.USER_COURSES_DIR.exists():
            for item in config.USER_COURSES_DIR.iterdir():
                if item.is_dir():
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                                courses.append({
                                    "course_id": item.name,
                                    "title": metadata.get("title", item.name),
                                    "domain": metadata.get("domain", "Unknown"),
                                    "description": metadata.get("description", ""),
                                    "type": "user-created"
                                })
                        except Exception as e:
                            logger.warning(f"Could not load metadata for user course {item.name}: {e}")

        return {
            "courses": courses,
            "total": len(courses)
        }

    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list courses: {str(e)}"
        )


@app.get("/courses/{course_id}", response_model=CourseMetadata)
async def get_course(course_id: str):
    """
    Get detailed metadata for a specific course.

    Args:
        course_id: Course identifier

    Returns:
        Course metadata including concepts
    """
    try:
        course_dir = config.get_course_dir(course_id)
        metadata_file = course_dir / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Load concepts list
        concepts = []
        if course_dir.exists():
            for item in sorted(course_dir.iterdir()):
                if item.is_dir() and item.name.startswith("concept-"):
                    concept_metadata_file = item / "metadata.json"
                    if concept_metadata_file.exists():
                        try:
                            with open(concept_metadata_file, "r", encoding="utf-8") as f:
                                concept_meta = json.load(f)
                                concepts.append({
                                    "concept_id": item.name,
                                    "title": concept_meta.get("title", item.name)
                                })
                        except Exception as e:
                            logger.warning(f"Could not load concept metadata for {item.name}: {e}")

        return {
            "course_id": course_id,
            "title": metadata.get("title", course_id),
            "domain": metadata.get("domain", "Unknown"),
            "description": metadata.get("description", ""),
            "target_audience": metadata.get("target_audience", "general"),
            "created_at": metadata.get("created_at", ""),
            "updated_at": metadata.get("updated_at", ""),
            "concepts": concepts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course: {str(e)}"
        )


@app.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(body: CreateCourseRequest):
    """
    Create a new user course.

    Args:
        body: Course creation request with metadata and concepts

    Returns:
        Created course metadata
    """
    try:
        # Course will be created in user-courses directory
        course_dir = config.USER_COURSES_DIR / body.course_id

        if course_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course {body.course_id} already exists"
            )

        # Create course directory
        course_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata
        metadata = {
            "course_id": body.course_id,
            "title": body.title,
            "domain": body.domain,
            "taxonomy": body.taxonomy,
            "course_learning_outcomes": body.course_learning_outcomes,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "user-created"
        }

        # Add optional fields for backward compatibility
        if body.description:
            metadata["description"] = body.description
        if body.target_audience:
            metadata["target_audience"] = body.target_audience

        # Save metadata
        metadata_file = course_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Create concepts if provided
        for i, concept_data in enumerate(body.concepts):
            concept_id = f"concept-{str(i + 1).zfill(3)}"
            concept_dir = course_dir / concept_id
            concept_dir.mkdir(parents=True, exist_ok=True)

            # Create concept metadata
            concept_metadata = {
                "concept_id": concept_id,
                "title": concept_data.get("title", f"Concept {i + 1}"),
                "module_learning_outcomes": concept_data.get("moduleLearningOutcomes", []),
                "prerequisites": concept_data.get("prerequisites", [])
            }

            # Support old field name for backward compatibility
            if not concept_metadata["module_learning_outcomes"] and "learningObjectives" in concept_data:
                concept_metadata["module_learning_outcomes"] = concept_data.get("learningObjectives", [])

            concept_metadata_file = concept_dir / "metadata.json"
            with open(concept_metadata_file, "w", encoding="utf-8") as f:
                json.dump(concept_metadata, f, indent=2, ensure_ascii=False)

            # Create resources directory
            resources_dir = concept_dir / "resources"
            resources_dir.mkdir(parents=True, exist_ok=True)

            # Create text-explainer.md
            text_explainer_file = resources_dir / "text-explainer.md"
            teaching_content = concept_data.get("teachingContent", "")
            with open(text_explainer_file, "w", encoding="utf-8") as f:
                f.write(teaching_content)

            # Create examples.json
            examples_file = resources_dir / "examples.json"
            vocabulary = concept_data.get("vocabulary", [])
            examples_data = {
                "examples": [
                    {
                        "term": v.get("term", ""),
                        "definition": v.get("definition", ""),
                        "example": v.get("example", "")
                    }
                    for v in vocabulary
                ]
            }
            with open(examples_file, "w", encoding="utf-8") as f:
                json.dump(examples_data, f, indent=2, ensure_ascii=False)

            # Create assessments directory (placeholder for now)
            assessments_dir = concept_dir / "assessments"
            assessments_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created new course: {body.course_id}")

        return {
            "success": True,
            "message": f"Course {body.course_id} created successfully",
            "course_id": body.course_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )


# ============================================================================
# Source Management Endpoints
# ============================================================================

@app.post("/courses/{course_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def add_course_source(course_id: str, body: AddSourceRequest):
    """
    Add an external source to a course (course-level resource).

    Args:
        course_id: Course identifier
        body: Source URL and optional metadata

    Returns:
        Extracted source metadata
    """
    try:
        from .source_extraction import extract_source_metadata
        import uuid

        # Get course directory
        course_dir = config.get_course_dir(course_id)
        metadata_file = course_dir / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )

        # Load course metadata
        with open(metadata_file, "r", encoding="utf-8") as f:
            course_metadata = json.load(f)

        # Extract source metadata
        source_data = extract_source_metadata(body.url, body.source_type)

        # Override with custom title/description if provided
        if body.title:
            source_data["title"] = body.title
        if body.description:
            source_data["description"] = body.description

        # Generate unique source ID
        source_id = f"source-{uuid.uuid4().hex[:8]}"
        source_data["id"] = source_id

        # Add to course metadata
        if "sources" not in course_metadata:
            course_metadata["sources"] = []

        course_metadata["sources"].append(source_data)
        course_metadata["updated_at"] = datetime.now().isoformat()

        # Save updated metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(course_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Added source {source_id} to course {course_id}")

        return {
            "source_id": source_id,
            "type": source_data["type"],
            "url": source_data["url"],
            "title": source_data["title"],
            "description": source_data["description"],
            "metadata": source_data["metadata"],
            "added_at": source_data["added_at"],
            "status": source_data["status"],
            "error_message": source_data.get("error_message")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding source to course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add source: {str(e)}"
        )


@app.post("/courses/{course_id}/concepts/{concept_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def add_concept_source(course_id: str, concept_id: str, body: AddSourceRequest):
    """
    Add an external source to a specific concept.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        body: Source URL and optional metadata

    Returns:
        Extracted source metadata
    """
    try:
        from .source_extraction import extract_source_metadata
        import uuid

        # Get concept directory
        concept_dir = config.get_concept_dir(concept_id, course_id)
        metadata_file = concept_dir / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept {concept_id} not found in course {course_id}"
            )

        # Load concept metadata
        with open(metadata_file, "r", encoding="utf-8") as f:
            concept_metadata = json.load(f)

        # Extract source metadata
        source_data = extract_source_metadata(body.url, body.source_type)

        # Override with custom title/description if provided
        if body.title:
            source_data["title"] = body.title
        if body.description:
            source_data["description"] = body.description

        # Generate unique source ID
        source_id = f"source-{uuid.uuid4().hex[:8]}"
        source_data["id"] = source_id

        # Add to concept metadata
        if "sources" not in concept_metadata:
            concept_metadata["sources"] = []

        concept_metadata["sources"].append(source_data)

        # Save updated metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(concept_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Added source {source_id} to concept {concept_id} in course {course_id}")

        return {
            "source_id": source_id,
            "type": source_data["type"],
            "url": source_data["url"],
            "title": source_data["title"],
            "description": source_data["description"],
            "metadata": source_data["metadata"],
            "added_at": source_data["added_at"],
            "status": source_data["status"],
            "error_message": source_data.get("error_message")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding source to concept {concept_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add source: {str(e)}"
        )


@app.get("/sources/{source_id}/content", response_model=SourceContentResponse)
async def get_source_content(source_id: str, course_id: str, concept_id: Optional[str] = None):
    """
    Load full content from a source on-demand.

    Args:
        source_id: Source identifier
        course_id: Course identifier
        concept_id: Optional concept identifier (for concept-specific sources)

    Returns:
        Full source content
    """
    try:
        from .source_extraction import load_full_source_content

        # Find the source in metadata
        if concept_id:
            # Concept-level source
            concept_dir = config.get_concept_dir(concept_id, course_id)
            metadata_file = concept_dir / "metadata.json"
        else:
            # Course-level source
            course_dir = config.get_course_dir(course_id)
            metadata_file = course_dir / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metadata file not found"
            )

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Find source
        sources = metadata.get("sources", [])
        source = next((s for s in sources if s.get("id") == source_id), None)

        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found"
            )

        # Load full content
        content_data = load_full_source_content(source["url"], source["type"])

        return content_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading source content for {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load source content: {str(e)}"
        )


@app.delete("/courses/{course_id}/sources/{source_id}")
async def delete_course_source(course_id: str, source_id: str):
    """
    Remove a source from a course.

    Args:
        course_id: Course identifier
        source_id: Source identifier

    Returns:
        Success message
    """
    try:
        course_dir = config.get_course_dir(course_id)
        metadata_file = course_dir / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )

        # Load course metadata
        with open(metadata_file, "r", encoding="utf-8") as f:
            course_metadata = json.load(f)

        # Remove source
        sources = course_metadata.get("sources", [])
        original_count = len(sources)
        course_metadata["sources"] = [s for s in sources if s.get("id") != source_id]

        if len(course_metadata["sources"]) == original_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found"
            )

        course_metadata["updated_at"] = datetime.now().isoformat()

        # Save updated metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(course_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Deleted source {source_id} from course {course_id}")

        return {
            "success": True,
            "message": f"Source {source_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )


# ============================================================================
# Content Cache Statistics Endpoints
# ============================================================================

@app.get("/cache/stats")
async def get_cache_statistics(course_id: Optional[str] = None):
    """
    Get statistics about content cache usage and cost savings.

    Args:
        course_id: Optional course filter

    Returns:
        Cache statistics including hits, effectiveness, and cost savings
    """
    try:
        from .content_cache import get_cache_stats

        stats = get_cache_stats(course_id)

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
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


