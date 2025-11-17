"""
FastAPI Application for Latin Adaptive Learning System

Main application with REST API endpoints for the adaptive learning tutor.
"""

import os
import json
import logging
import io
from typing import Optional, List, Dict, Any
from datetime import datetime
from anthropic import Anthropic
from fastapi import FastAPI, HTTPException, status, Request, Depends, UploadFile, File
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
    course_id: Optional[str] = Field(None, description="Course ID to enroll in")


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
    difficulty: str  # Can be string like "medium" or "easy"
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
    # Support both flat concepts (old) and module-based structure (new)
    concepts: List[dict] = Field(default=[], description="Flat list of course concepts (deprecated - use modules)")
    modules: List[dict] = Field(default=[], description="Module-based course structure (each module contains concepts)")


class ImportCourseRequest(BaseModel):
    """Request to import a course from exported JSON."""
    export_data: dict = Field(..., description="Exported course JSON data")
    new_course_id: Optional[str] = Field(default=None, description="Optional new course ID (overrides exported ID)")
    overwrite: bool = Field(default=False, description="Overwrite existing course if it exists")


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
            profile=body.profile,
            course_id=body.course_id
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
async def get_concept_info(concept_id: str, course_id: Optional[str] = None, learner_id: Optional[str] = None):
    """
    Get information about a specific concept.

    Args:
        concept_id: Concept identifier
        course_id: Optional course ID
        learner_id: Optional learner ID to use their current course

    Returns metadata including title, objectives, vocabulary, etc.
    """
    try:
        # If learner_id is provided, use their current course
        if learner_id and not course_id:
            try:
                learner_model = load_learner_model(learner_id)
                course_id = learner_model.get("current_course")
                logger.info(f"Using learner {learner_id}'s current course: {course_id}")
            except Exception as e:
                logger.warning(f"Could not load learner {learner_id}'s course: {e}")

        metadata = load_concept_metadata(concept_id, course_id)

        return {
            "concept_id": metadata.get("concept_id", concept_id),
            "title": metadata.get("title", concept_id),
            "difficulty": metadata.get("difficulty", "medium"),
            "prerequisites": metadata.get("prerequisites", []),
            "learning_objectives": metadata.get("learning_objectives", metadata.get("module_learning_outcomes", [])),
            "estimated_mastery_time": metadata.get("estimated_mastery_time", "unknown"),
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
async def list_concepts(course_id: Optional[str] = None, learner_id: Optional[str] = None):
    """
    List all available concepts.

    Args:
        course_id: Optional course ID to list concepts for
        learner_id: Optional learner ID to use their current course

    Returns a list of all concept IDs for the specified or default course.
    """
    try:
        # If learner_id is provided, use their current course
        if learner_id and not course_id:
            try:
                learner_model = load_learner_model(learner_id)
                course_id = learner_model.get("current_course")
                logger.info(f"Using learner {learner_id}'s current course: {course_id}")
            except Exception as e:
                logger.warning(f"Could not load learner {learner_id}'s course: {e}")

        concepts = list_all_concepts(course_id)
        return {
            "success": True,
            "concepts": concepts,
            "total": len(concepts),
            "course_id": course_id or config.DEFAULT_COURSE_ID
        }

    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list concepts: {str(e)}"
        )


@app.get("/modules")
async def list_modules(course_id: Optional[str] = None, learner_id: Optional[str] = None):
    """
    List all modules in a course with their concepts.

    Args:
        course_id: Optional course ID to list modules for
        learner_id: Optional learner ID to use their current course

    Returns a list of modules with their metadata and concepts.
    """
    try:
        # If learner_id is provided, use their current course
        if learner_id and not course_id:
            try:
                learner_model = load_learner_model(learner_id)
                course_id = learner_model.get("current_course")
                logger.info(f"Using learner {learner_id}'s current course: {course_id}")
            except Exception as e:
                logger.warning(f"Could not load learner {learner_id}'s course: {e}")

        from .tools import list_all_modules
        modules = list_all_modules(course_id)
        return {
            "success": True,
            "modules": modules,
            "total": len(modules),
            "course_id": course_id or config.DEFAULT_COURSE_ID
        }

    except Exception as e:
        logger.error(f"Error listing modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list modules: {str(e)}"
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


@app.put("/learner/{learner_id}/practice-mode")
async def toggle_practice_mode(learner_id: str, body: dict):
    """
    Toggle practice mode for the learner.

    Practice mode allows learners to explore questions without affecting their mastery score.
    This provides choice and agency - learners can practice stress-free or work toward mastery.
    """
    try:
        from .tools import load_learner_model, save_learner_model

        # Get the practice mode value
        practice_mode = body.get("practiceMode")

        if practice_mode is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="practiceMode field is required (boolean)"
            )

        if not isinstance(practice_mode, bool):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="practiceMode must be a boolean value"
            )

        # Load learner model
        model = load_learner_model(learner_id)

        # Update practice mode
        old_mode = model.get("practice_mode", False)
        model["practice_mode"] = practice_mode

        # Save updated model
        save_learner_model(learner_id, model)

        logger.info(f"✅ Updated practice mode for {learner_id}: {old_mode} → {practice_mode}")

        return {
            "success": True,
            "message": f"Practice mode {'enabled' if practice_mode else 'disabled'}",
            "previous_mode": old_mode,
            "new_mode": practice_mode
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating practice mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update practice mode: {str(e)}"
        )


@app.post("/request-hint")
async def request_hint(request: Request, body: dict):
    """
    Generate a hint for the current question (practice mode only).

    Provides graduated hints:
    - Level 1 (gentle): Indirect nudge toward the concept
    - Level 2 (direct): Specific guidance on what to look for
    - Level 3 (answer): Show answer with explanation

    Args:
        body: Must include learner_id, concept_id, question_context, hint_level
    """
    try:
        from .tools import load_learner_model
        from .content_generators import generate_hint_request
        from .agent import call_claude_api
        from .constants import (
            HINTS_ENABLED_IN_PRACTICE,
            HINTS_ENABLED_IN_GRADED,
            HINT_LEVEL_GENTLE,
            HINT_LEVEL_DIRECT,
            HINT_LEVEL_ANSWER
        )

        learner_id = body.get("learner_id")
        concept_id = body.get("concept_id")
        question_context = body.get("question_context")  # scenario, question, options, correct_answer
        hint_level = body.get("hint_level", HINT_LEVEL_GENTLE)

        if not all([learner_id, concept_id, question_context]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="learner_id, concept_id, and question_context are required"
            )

        # Validate hint level
        valid_levels = [HINT_LEVEL_GENTLE, HINT_LEVEL_DIRECT, HINT_LEVEL_ANSWER]
        if hint_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"hint_level must be one of: {', '.join(valid_levels)}"
            )

        # Load learner model to check practice mode
        learner_model = load_learner_model(learner_id)
        practice_mode = learner_model.get("practice_mode", False)

        # Check if hints are allowed in current mode
        if practice_mode and not HINTS_ENABLED_IN_PRACTICE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hints are disabled in practice mode"
            )

        if not practice_mode and not HINTS_ENABLED_IN_GRADED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hints are only available in practice mode. Enable practice mode to request hints."
            )

        # Generate hint prompt
        hint_prompt = generate_hint_request(question_context, hint_level, concept_id)

        # Call Claude API for hint
        response = call_claude_api(
            system_prompt="You are a patient Latin tutor providing hints to a struggling student in practice mode. Be encouraging and educational.",
            user_message=hint_prompt,
            model=config.CLAUDE_MODEL,
            max_tokens=500  # Hints should be brief
        )

        # Extract hint text (response should be plain text, not JSON)
        hint_text = response.get("content", [{}])[0].get("text", "")

        if not hint_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate hint"
            )

        logger.info(f"Generated {hint_level} hint for {learner_id}, {concept_id}")

        return {
            "success": True,
            "hint_level": hint_level,
            "hint_text": hint_text,
            "practice_mode": practice_mode
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner not found: {learner_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating hint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hint: {str(e)}"
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

        # Load learner model to check practice mode and detect struggle/celebration
        from .tools import (
            record_assessment_and_check_completion,
            load_learner_model,
            detect_struggle,
            detect_celebration_milestones
        )

        learner_model = load_learner_model(body.learner_id)
        practice_mode = learner_model.get("practice_mode", False)

        # Record assessment and check for concept completion
        completion_result = record_assessment_and_check_completion(
            learner_id=body.learner_id,
            concept_id=body.current_concept,
            is_correct=is_correct,
            confidence=body.confidence,
            question_type=body.question_type,
            practice_mode=practice_mode
        )

        # Detect if learner is struggling and provide encouragement
        struggle_info = detect_struggle(body.learner_id, body.current_concept) if not is_correct else None

        # Detect celebration-worthy milestones (streaks, completions, comebacks)
        celebration_info = detect_celebration_milestones(
            learner_id=body.learner_id,
            concept_id=body.current_concept,
            is_correct=is_correct,
            concept_completed=completion_result.get("concept_completed", False),
            concepts_completed_total=completion_result.get("concepts_completed_total", 0)
        ) if is_correct else None

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
            error_detail = result.get("error", "Unknown error")
            logger.error(f"Content generation failed: {error_detail}")
            if "error_details" in result:
                logger.error(f"Error details: {result['error_details']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate next content: {error_detail}"
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

        # Add encouragement message if learner is struggling
        encouragement_message = None
        if struggle_info:
            encouragement_message = struggle_info.get("encouragement_message")
            logger.info(f"Encouragement message: {encouragement_message}")

        # Add celebration message if milestone achieved
        celebration_message = None
        if celebration_info:
            celebration_message = celebration_info.get("celebration_message")
            logger.info(f"Celebration message: {celebration_message}")

        # Get user's answer display text
        user_answer_display = body.user_answer
        if body.question_type == "multiple-choice" and body.options and isinstance(body.user_answer, int):
            if 0 <= body.user_answer < len(body.options):
                user_answer_display = body.options[body.user_answer]

        assessment_result = {
            "type": "assessment-result",
            "score": 1.0 if is_correct else 0.0,
            "feedback": feedback_text,
            "correctAnswer": correct_answer_display if body.question_type != "dialogue" else None,
            "userAnswer": user_answer_display,
            "calibration": calibration_type,
            "languageConnection": language_connection,
            "encouragement": encouragement_message,  # Add encouragement for struggling learners
            "celebration": celebration_message,  # Add celebration for milestones
            "practiceMode": practice_mode,  # Indicate if this was practice mode
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
            "practice_mode": practice_mode,  # Add to main response
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


@app.get("/courses/{course_id}")
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

        # Load concepts list using the helper function (handles both module and flat structures)
        concept_ids = list_all_concepts(course_id)
        concepts = []

        for concept_id in concept_ids:
            try:
                concept_meta = load_concept_metadata(concept_id, course_id)
                concepts.append({
                    "concept_id": concept_id,
                    "title": concept_meta.get("title", concept_id)
                })
            except Exception as e:
                logger.warning(f"Could not load concept metadata for {concept_id}: {e}")

        return {
            "success": True,
            "course": {
                "course_id": course_id,
                "title": metadata.get("title", course_id),
                "domain": metadata.get("domain", "Unknown"),
                "description": metadata.get("description", ""),
                "target_audience": metadata.get("target_audience", "general"),
                "course_learning_outcomes": metadata.get("course_learning_outcomes", []),
                "created_at": metadata.get("created_at", ""),
                "updated_at": metadata.get("updated_at", ""),
                "concepts": concepts
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course: {str(e)}"
        )


@app.get("/courses/{course_id}/export")
async def export_course(course_id: str):
    """
    Export complete course data as JSON for backup/sharing.

    Returns all course metadata, modules, concepts, and external resources
    in a single JSON structure that can be imported later.

    Args:
        course_id: Course identifier

    Returns:
        Complete course export JSON
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

        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "course": {
                "course_id": course_metadata.get("course_id"),
                "title": course_metadata.get("title"),
                "domain": course_metadata.get("domain"),
                "taxonomy": course_metadata.get("taxonomy", "blooms"),
                "course_learning_outcomes": course_metadata.get("course_learning_outcomes", []),
                "description": course_metadata.get("description"),
                "target_audience": course_metadata.get("target_audience"),
                "created_at": course_metadata.get("created_at"),
                "updated_at": course_metadata.get("updated_at")
            },
            "modules": [],
            "external_resources": []
        }

        # Load modules if they exist
        modules_dir = course_dir / "modules"
        if modules_dir.exists() and modules_dir.is_dir():
            module_dirs = sorted([d for d in modules_dir.iterdir() if d.is_dir()])

            for module_dir in module_dirs:
                module_metadata_file = module_dir / "metadata.json"
                if module_metadata_file.exists():
                    with open(module_metadata_file, "r", encoding="utf-8") as f:
                        module_metadata = json.load(f)

                    module_export = {
                        "id": module_metadata.get("id"),
                        "title": module_metadata.get("title"),
                        "module_learning_outcomes": module_metadata.get("module_learning_outcomes", []),
                        "concepts": []
                    }

                    # Load concepts within this module
                    concept_ids = module_metadata.get("concepts", [])
                    for concept_id in concept_ids:
                        concept_dir = module_dir / concept_id
                        concept_metadata_file = concept_dir / "metadata.json"

                        if concept_metadata_file.exists():
                            with open(concept_metadata_file, "r", encoding="utf-8") as f:
                                concept_metadata = json.load(f)

                            module_export["concepts"].append({
                                "concept_id": concept_metadata.get("concept_id"),
                                "title": concept_metadata.get("title"),
                                "learning_objectives": concept_metadata.get("learning_objectives", []),
                                "prerequisites": concept_metadata.get("prerequisites", [])
                            })

                    export_data["modules"].append(module_export)

        # Load external resources if they exist
        external_resources_file = config.RESOURCE_BANK_DIR / "external-resources.json"
        if external_resources_file.exists():
            with open(external_resources_file, "r", encoding="utf-8") as f:
                all_resources = json.load(f)

            # Filter resources relevant to this course's concepts
            concept_ids = list_all_concepts(course_id)
            for concept_id in concept_ids:
                if concept_id in all_resources:
                    export_data["external_resources"].append({
                        "concept_id": concept_id,
                        "resources": all_resources[concept_id].get("resources", [])
                    })

        return {
            "success": True,
            "export": export_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export course: {str(e)}"
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

        # Create module-based structure if modules are provided, otherwise fall back to flat concepts
        if body.modules and len(body.modules) > 0:
            # Module-based structure
            for module_index, module_data in enumerate(body.modules):
                module_id = module_data.get("moduleId", f"module-{str(module_index + 1).zfill(3)}")
                module_dir = course_dir / module_id
                module_dir.mkdir(parents=True, exist_ok=True)

                # Create module metadata
                module_metadata = {
                    "id": module_id,
                    "title": module_data.get("title", f"Module {module_index + 1}"),
                    "module_learning_outcomes": module_data.get("moduleLearningOutcomes", [])
                }

                module_metadata_file = module_dir / "metadata.json"
                with open(module_metadata_file, "w", encoding="utf-8") as f:
                    json.dump(module_metadata, f, indent=2, ensure_ascii=False)

                # Create concepts within this module
                for concept_index, concept_data in enumerate(module_data.get("concepts", [])):
                    concept_id = concept_data.get("conceptId", f"concept-{str(concept_index + 1).zfill(3)}")
                    concept_dir = module_dir / concept_id
                    concept_dir.mkdir(parents=True, exist_ok=True)

                    # Create concept metadata
                    concept_metadata = {
                        "concept_id": concept_id,
                        "title": concept_data.get("title", f"Concept {concept_index + 1}"),
                        "learning_objectives": concept_data.get("learningObjectives", concept_data.get("moduleLearningOutcomes", [])),
                        "prerequisites": concept_data.get("prerequisites", [])
                    }

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

        else:
            # Flat concept structure (backward compatibility)
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


@app.post("/courses/import", status_code=status.HTTP_201_CREATED)
async def import_course(body: ImportCourseRequest):
    """
    Import a course from exported JSON.

    Args:
        body: Import request with export data and optional overrides

    Returns:
        Success message with imported course ID
    """
    try:
        export_data = body.export_data

        # Validate export data structure
        if "export" not in export_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format: missing 'export' key"
            )

        export_content = export_data["export"]
        if "course" not in export_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format: missing 'course' key"
            )

        course_data = export_content["course"]
        modules_data = export_content.get("modules", [])

        # Determine course ID (use override or original)
        course_id = body.new_course_id or course_data.get("course_id")
        if not course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course ID is required"
            )

        # Check if course already exists
        course_dir = config.USER_COURSES_DIR / course_id
        if course_dir.exists() and not body.overwrite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course {course_id} already exists. Use overwrite=true to replace."
            )

        # Create or clean course directory
        if body.overwrite and course_dir.exists():
            import shutil
            shutil.rmtree(course_dir)

        course_dir.mkdir(parents=True, exist_ok=True)

        # Create course metadata
        course_metadata = {
            "course_id": course_id,
            "title": course_data.get("title"),
            "domain": course_data.get("domain"),
            "taxonomy": course_data.get("taxonomy", "blooms"),
            "course_learning_outcomes": course_data.get("course_learning_outcomes", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "user-created",
            "imported_from": course_data.get("course_id"),
            "original_created_at": course_data.get("created_at")
        }

        # Add optional fields
        if course_data.get("description"):
            course_metadata["description"] = course_data.get("description")
        if course_data.get("target_audience"):
            course_metadata["target_audience"] = course_data.get("target_audience")

        # Save course metadata
        metadata_file = course_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(course_metadata, f, indent=2, ensure_ascii=False)

        # Create modules structure
        if modules_data:
            modules_dir = course_dir / "modules"
            modules_dir.mkdir(exist_ok=True)

            for module_data in modules_data:
                module_id = module_data.get("id")
                if not module_id:
                    continue

                module_dir = modules_dir / module_id
                module_dir.mkdir(parents=True, exist_ok=True)

                # Create module metadata
                module_metadata = {
                    "id": module_id,
                    "title": module_data.get("title"),
                    "module_learning_outcomes": module_data.get("module_learning_outcomes", []),
                    "concepts": []
                }

                # Create concepts within module
                concepts_data = module_data.get("concepts", [])
                for concept_data in concepts_data:
                    concept_id = concept_data.get("concept_id")
                    if not concept_id:
                        continue

                    module_metadata["concepts"].append(concept_id)

                    # Create concept directory
                    concept_dir = module_dir / concept_id
                    concept_dir.mkdir(parents=True, exist_ok=True)

                    # Create assessments and resources directories
                    (concept_dir / "assessments").mkdir(exist_ok=True)
                    (concept_dir / "resources").mkdir(exist_ok=True)

                    # Create concept metadata
                    concept_metadata = {
                        "concept_id": concept_id,
                        "title": concept_data.get("title"),
                        "learning_objectives": concept_data.get("learning_objectives", []),
                        "prerequisites": concept_data.get("prerequisites", [])
                    }

                    concept_metadata_file = concept_dir / "metadata.json"
                    with open(concept_metadata_file, "w", encoding="utf-8") as f:
                        json.dump(concept_metadata, f, indent=2, ensure_ascii=False)

                # Save module metadata
                module_metadata_file = module_dir / "metadata.json"
                with open(module_metadata_file, "w", encoding="utf-8") as f:
                    json.dump(module_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully imported course: {course_id}")

        return {
            "success": True,
            "message": f"Course '{course_id}' imported successfully",
            "course_id": course_id,
            "modules_count": len(modules_data),
            "total_concepts": sum(len(m.get("concepts", [])) for m in modules_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import course: {str(e)}"
        )


@app.post("/courses/parse-syllabus")
async def parse_syllabus(file: UploadFile = File(...), domain: Optional[str] = None, taxonomy: str = "blooms"):
    """
    Upload and parse a syllabus document to extract course structure.

    Supports PDF and text files. Uses AI to extract:
    - Course title
    - Subject domain
    - Course learning outcomes
    - Module/topic structure
    - Suggested concept breakdowns

    Args:
        file: Uploaded syllabus file (PDF or text)
        domain: Optional domain/subject area hint
        taxonomy: Learning taxonomy to use (blooms, finks, or both)

    Returns:
        Extracted course structure ready for import
    """
    try:
        # Read file content
        content = await file.read()

        # Determine file type and extract text
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension == 'txt':
            # Plain text file
            syllabus_text = content.decode('utf-8')
        elif file_extension == 'pdf':
            # PDF file - for now, just return an error asking for text
            # In production, you'd use PyPDF2 or similar
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF parsing not yet implemented. Please upload a .txt file or paste text directly."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Please upload .txt or .pdf files."
            )

        if len(syllabus_text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Syllabus content too short. Please provide a complete syllabus document."
            )

        # Use Claude to extract course structure
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

        extraction_prompt = f"""You are an expert instructional designer analyzing a course syllabus. Extract structured course information from the following syllabus.

Syllabus Content:
{syllabus_text}

Please analyze this syllabus and extract:

1. **Course Title**: The official course name
2. **Subject Domain**: The academic field (e.g., Mathematics, Computer Science, Business, etc.){f" Hint: {domain}" if domain else ""}
3. **Course Learning Outcomes (CLOs)**: 3-5 broad, measurable outcomes students should achieve by completing the course. Use {taxonomy} taxonomy action verbs.
4. **Modules/Topics**: Break down the course into 3-7 logical modules or topic areas
5. **For each module**:
   - Module title
   - 3-5 module learning outcomes (MLOs) using {taxonomy} taxonomy
   - Suggested concepts to cover (2-5 concepts per module)

Return your response in valid JSON format:
{{
  "course_title": "...",
  "domain": "...",
  "course_learning_outcomes": ["...", "...", "..."],
  "modules": [
    {{
      "title": "...",
      "module_learning_outcomes": ["...", "...", "..."],
      "concepts": [
        {{
          "title": "...",
          "learning_objectives": ["...", "..."]
        }}
      ]
    }}
  ]
}}

Important:
- Extract outcomes that are measurable and use appropriate action verbs from {taxonomy} taxonomy
- Infer module structure even if not explicitly stated in the syllabus
- Keep concept titles concise (3-8 words)
- Ensure learning objectives are specific and measurable"""

        logger.info(f"Using model for syllabus parsing: {config.ANTHROPIC_MODEL}")
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": extraction_prompt
            }]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Could not extract JSON from AI response")

        extracted_data = json.loads(json_match.group())

        # Validate required fields
        if not all(key in extracted_data for key in ['course_title', 'domain', 'modules']):
            raise ValueError("Incomplete extraction - missing required fields")

        # Transform to wizard format with auto-generated IDs
        modules_with_ids = []
        for i, module in enumerate(extracted_data.get('modules', [])):
            module_id = f"module-{str(i+1).zfill(3)}"
            concepts_with_ids = []

            for j, concept in enumerate(module.get('concepts', [])):
                concept_id = f"concept-{str(j+1).zfill(3)}"
                concepts_with_ids.append({
                    "conceptId": concept_id,
                    "title": concept.get('title', f'Concept {j+1}'),
                    "learningObjectives": concept.get('learning_objectives', []),
                    "prerequisites": [],
                    "teachingContent": "",
                    "vocabulary": []
                })

            modules_with_ids.append({
                "moduleId": module_id,
                "title": module.get('title', f'Module {i+1}'),
                "moduleLearningOutcomes": module.get('module_learning_outcomes', []),
                "concepts": concepts_with_ids
            })

        result = {
            "success": True,
            "extracted_data": {
                "title": extracted_data.get('course_title', 'Untitled Course'),
                "domain": extracted_data.get('domain', domain or 'Unknown'),
                "taxonomy": taxonomy,
                "courseLearningOutcomes": extracted_data.get('course_learning_outcomes', []),
                "modules": modules_with_ids
            },
            "raw_extraction": extracted_data
        }

        logger.info(f"Successfully parsed syllabus: {file.filename}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error parsing syllabus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse syllabus: {str(e)}"
        )


class GenerateLearningOutcomesRequest(BaseModel):
    """Request body for generating learning outcomes."""
    description: str = Field(..., description="Description of the course, module, or concept")
    taxonomy: str = Field(default="blooms", description="Learning taxonomy framework (blooms or finks)")
    level: str = Field(..., description="Level of outcomes: course, module, or concept")
    count: Optional[int] = Field(default=5, description="Number of outcomes to generate")
    existing_outcomes: Optional[List[str]] = Field(default=None, description="Existing outcomes to consider")


class GenerateLearningOutcomesResponse(BaseModel):
    """Response with generated learning outcomes."""
    success: bool
    outcomes: List[str]
    taxonomy: str
    level: str


@app.post("/generate-learning-outcomes", response_model=GenerateLearningOutcomesResponse)
async def generate_learning_outcomes(body: GenerateLearningOutcomesRequest):
    """
    Generate learning outcomes using AI based on description and taxonomy.

    Args:
        body: Request with description, taxonomy, level, and count

    Returns:
        List of generated learning outcomes
    """
    try:
        logger.info(f"Generating {body.count} {body.level}-level outcomes using {body.taxonomy} taxonomy")
        logger.info(f"Description length: {len(body.description)} characters")

        # Build taxonomy-specific guidance
        taxonomy_guidance = ""
        if body.taxonomy == "blooms":
            taxonomy_guidance = """
Use Bloom's Taxonomy (revised) with these cognitive levels:
- Remember: Recall facts and basic concepts
- Understand: Explain ideas or concepts
- Apply: Use information in new situations
- Analyze: Draw connections among ideas
- Evaluate: Justify a stand or decision
- Create: Produce new or original work

Start each outcome with an appropriate action verb for the cognitive level.
Examples: "Define", "Explain", "Apply", "Analyze", "Evaluate", "Create"
"""
        elif body.taxonomy == "finks":
            taxonomy_guidance = """
Use Fink's Taxonomy of Significant Learning with these dimensions:
- Foundational Knowledge: Understanding and remembering information
- Application: Skills, thinking, managing projects
- Integration: Connecting ideas, people, realms of life
- Human Dimension: Learning about oneself and others
- Caring: Developing new feelings, interests, values
- Learning How to Learn: Becoming a better student, inquiring, self-directing

Each outcome should address one or more dimensions of significant learning.
"""

        # Build level-specific guidance
        level_guidance = ""
        if body.level == "course":
            level_guidance = "These are COURSE Learning Outcomes (CLOs) - broad, overarching goals for the entire course."
        elif body.level == "module":
            level_guidance = "These are MODULE Learning Outcomes (MLOs) - specific goals for this module that contribute to course outcomes."
        elif body.level == "concept":
            level_guidance = "These are CONCEPT Learning Objectives - granular, measurable objectives for a single concept or topic."

        # Build the prompt
        prompt = f"""You are an expert instructional designer creating learning outcomes.

{level_guidance}

{taxonomy_guidance}

DESCRIPTION:
{body.description}

REQUIREMENTS:
- Generate exactly {body.count} learning outcomes
- Each outcome must be:
  * Measurable and specific
  * Use appropriate action verbs for {body.taxonomy} taxonomy
  * Clear and concise (1-2 sentences maximum)
  * Focus on what learners will be able to do
"""

        if body.existing_outcomes:
            prompt += f"""
EXISTING OUTCOMES TO AVOID DUPLICATING:
{chr(10).join(f"- {outcome}" for outcome in body.existing_outcomes)}

Generate NEW outcomes that complement but don't duplicate the existing ones.
"""

        prompt += """
Respond with ONLY a JSON object in this exact format:
{
  "outcomes": [
    "First learning outcome here",
    "Second learning outcome here",
    "Third learning outcome here"
  ]
}

Do not include any explanation or additional text - ONLY the JSON object.
"""

        # Call Claude API
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info(f"Using model for outcome generation: {config.ANTHROPIC_MODEL}")

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,  # Slightly creative for varied suggestions
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract the text response
        response_text = response.content[0].text.strip()
        logger.info(f"AI response: {response_text[:200]}...")

        # Parse JSON response
        try:
            result = json.loads(response_text)
            outcomes = result.get("outcomes", [])

            if not outcomes:
                raise ValueError("No outcomes generated in response")

            logger.info(f"Successfully generated {len(outcomes)} outcomes")

            return GenerateLearningOutcomesResponse(
                success=True,
                outcomes=outcomes,
                taxonomy=body.taxonomy,
                level=body.level
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response as JSON: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Error generating learning outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning outcomes: {str(e)}"
        )


@app.post("/courses/import-cartridge")
async def import_common_cartridge(file: UploadFile = File(...)):
    """
    Import course from Common Cartridge (.imscc) file.

    Parses IMS Common Cartridge exports from Canvas, Moodle, Blackboard, etc.
    Extracts course structure, modules, content, and returns data for course wizard.

    Args:
        file: Common Cartridge file (.imscc or .zip)

    Returns:
        Extracted course data in wizard format
    """
    try:
        logger.info(f"Importing Common Cartridge: {file.filename}")

        # Validate file type
        if not file.filename.endswith(('.imscc', '.zip')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a .imscc or .zip file"
            )

        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )

        # Save to temporary file
        import tempfile
        from pathlib import Path
        from .cartridge_parser import parse_common_cartridge

        with tempfile.NamedTemporaryFile(delete=False, suffix='.imscc') as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        try:
            # Parse the cartridge
            logger.info(f"Parsing cartridge file: {tmp_path}")
            extracted_data = parse_common_cartridge(tmp_path)

            logger.info(f"Successfully parsed cartridge: {extracted_data.get('title', 'Unknown')}")
            logger.info(f"Extracted {len(extracted_data.get('modules', []))} modules")

            return {
                "success": True,
                "extracted_data": extracted_data,
                "message": f"Successfully imported course: {extracted_data.get('title', 'Unknown')}"
            }

        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error importing Common Cartridge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import Common Cartridge: {str(e)}"
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

        # Add requirement and verification data
        source_data["requirement_level"] = body.requirement_level
        source_data["verification_method"] = body.verification_method
        if body.verification_data:
            source_data["verification_data"] = body.verification_data

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

        # Add requirement and verification data
        source_data["requirement_level"] = body.requirement_level
        source_data["verification_method"] = body.verification_method
        if body.verification_data:
            source_data["verification_data"] = body.verification_data

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
# AI Course Generation Endpoints
# ============================================================================

class GenerateModuleLearningOutcomesRequest(BaseModel):
    module_title: str
    course_title: str
    course_learning_outcomes: list
    domain: str
    taxonomy: str = "blooms"

@app.post("/generate-module-learning-outcomes")
async def generate_module_learning_outcomes(body: GenerateModuleLearningOutcomesRequest):
    """
    Generate module learning outcomes using AI based on module context and course CLOs.

    Args:
        module_title: Module title
        course_title: Parent course title
        course_learning_outcomes: List of course-level learning outcomes for context
        domain: Subject area/domain
        taxonomy: Learning taxonomy (blooms or finks)

    Returns:
        List of suggested module learning outcomes
    """
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

        # Build taxonomy-specific guidance
        taxonomy_guidance = ""
        if body.taxonomy == "blooms":
            taxonomy_guidance = """
Use Bloom's Taxonomy action verbs at appropriate levels:
- Remember: define, identify, list, recall, recognize
- Understand: classify, describe, discuss, explain, summarize
- Apply: demonstrate, execute, implement, solve, use
- Analyze: categorize, compare, differentiate, examine, test
- Evaluate: appraise, critique, defend, judge, justify
- Create: compose, construct, design, develop, formulate
"""
        elif body.taxonomy == "finks":
            taxonomy_guidance = """
Use Fink's Taxonomy of Significant Learning dimensions:
- Foundational Knowledge: understanding and remembering information
- Application: skills, critical/creative thinking, managing projects
- Integration: connecting ideas, people, realms of life
- Human Dimension: learning about oneself and others
- Caring: developing new feelings, interests, values
- Learning How to Learn: becoming a better student, inquiring, self-directing
"""

        # Format CLOs for context
        clos_context = "\n".join([f"- {clo}" for clo in body.course_learning_outcomes])

        system_prompt = f"""You are an expert instructional designer specializing in creating measurable learning outcomes.

Generate exactly 3 high-quality Module Learning Outcomes (MLOs) for the following module:

Course: {body.course_title}
Module: {body.module_title}
Domain: {body.domain}
Taxonomy: {body.taxonomy}

Course Learning Outcomes (CLOs):
{clos_context}

{taxonomy_guidance}

Guidelines:
1. Each MLO should support one or more CLOs (be a building block toward course goals)
2. MLOs are narrower in scope than CLOs - focus on what this specific module covers
3. Use appropriate action verbs from the taxonomy
4. Focus on what learners will be able to DO after completing this module
5. Be specific and measurable
6. Be concise and clear (one sentence each)
7. Make them relevant to the module topic within the {body.domain} domain

Return ONLY a JSON array of outcome strings, no other text or explanation:
["outcome 1", "outcome 2", "outcome 3"]"""

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Generate module learning outcomes for: {body.module_title}"
            }]
        )

        # Parse response
        content_text = response.content[0].text.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if content_text.startswith("```"):
            lines = content_text.split("\n")
            content_text = "\n".join(lines[1:-1])

        outcomes = json.loads(content_text)

        # Ensure we don't exceed the maximum
        MAX_OUTCOMES = 3
        if len(outcomes) > MAX_OUTCOMES:
            logger.warning(f"AI generated {len(outcomes)} module outcomes, truncating to {MAX_OUTCOMES}")
            outcomes = outcomes[:MAX_OUTCOMES]

        logger.info(f"Generated {len(outcomes)} module learning outcomes for '{body.module_title}'")

        return {
            "success": True,
            "outcomes": outcomes
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse AI response"
        )
    except Exception as e:
        logger.error(f"Error generating module learning outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate module learning outcomes: {str(e)}"
        )


class GenerateConceptLearningObjectivesRequest(BaseModel):
    concept_title: str
    module_title: str
    module_learning_outcomes: list
    course_title: str
    domain: str
    taxonomy: str = "blooms"

@app.post("/generate-concept-learning-objectives")
async def generate_concept_learning_objectives(body: GenerateConceptLearningObjectivesRequest):
    """
    Generate concept learning objectives using AI based on concept and module context.
    """
    logger.info(f"Generating learning objectives for concept: {body.concept_title} in module: {body.module_title}")

    # Build context from module learning outcomes
    mlos_context = "\n".join([f"- {mlo}" for mlo in body.module_learning_outcomes if mlo.strip()])

    # Taxonomy guidance
    taxonomy_guidance = ""
    if body.taxonomy == "blooms":
        taxonomy_guidance = """
Use Bloom's Taxonomy action verbs at appropriate levels:
- Remember: identify, recall, list, define, describe
- Understand: explain, summarize, interpret, compare, classify
- Apply: demonstrate, solve, use, implement, execute
- Analyze: differentiate, organize, attribute, examine, deconstruct
- Evaluate: critique, judge, assess, defend, justify
- Create: design, construct, develop, formulate, compose
"""
    elif body.taxonomy == "finks":
        taxonomy_guidance = """
Use Fink's Taxonomy of Significant Learning:
- Foundational Knowledge: understand key concepts, remember information
- Application: develop skills, think critically, manage projects
- Integration: connect ideas, see relationships, transfer learning
- Human Dimension: learn about self and others
- Caring: develop interests, values, feelings
- Learning How to Learn: become better learners, inquire, self-direct
"""

    system_prompt = f"""You are an expert instructional designer specializing in creating measurable learning objectives.

Generate exactly 3 high-quality Learning Objectives for the following concept:

Course: {body.course_title}
Module: {body.module_title}
Concept: {body.concept_title}
Domain: {body.domain}
Taxonomy: {body.taxonomy}

Module Learning Outcomes (MLOs):
{mlos_context}

{taxonomy_guidance}

Guidelines:
1. Each objective should support one or more MLOs (be a building block toward module goals)
2. Objectives are very specific and granular - focus on what this particular concept teaches
3. Use appropriate action verbs from the taxonomy
4. Start each objective with "Students will be able to..." or use an action verb directly
5. Be specific and measurable (avoid vague terms like "understand" or "know")
6. Focus on observable behaviors and concrete skills
7. Consider the domain ({body.domain}) when crafting objectives

Example structure:
- "Identify the three key components of [specific concept]"
- "Apply [specific technique] to solve problems involving [specific topic]"
- "Analyze the relationship between [A] and [B] in the context of [specific scenario]"

Return ONLY a JSON array of exactly 3 learning objectives as strings. No other text or explanation.

Example format:
```json
[
  "Students will be able to identify the key features of...",
  "Students will be able to apply the concept to...",
  "Students will be able to analyze relationships between..."
]
```"""

    try:
        # Call Anthropic Claude API
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate exactly 3 learning objectives for the concept '{body.concept_title}' in the module '{body.module_title}'."
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text
        logger.info(f"AI Response: {response_text}")

        # Try to extract JSON from markdown code blocks if present
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            content_text = json_match.group(1)
        else:
            # Try to find raw JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                content_text = json_match.group(0)
            else:
                content_text = response_text

        objectives = json.loads(content_text)

        # Ensure we generate exactly 3 objectives
        MAX_OBJECTIVES = 3
        if len(objectives) > MAX_OBJECTIVES:
            logger.warning(f"AI generated {len(objectives)} objectives, truncating to {MAX_OBJECTIVES}")
            objectives = objectives[:MAX_OBJECTIVES]
        elif len(objectives) < MAX_OBJECTIVES:
            logger.warning(f"AI generated only {len(objectives)} objectives, expected {MAX_OBJECTIVES}")

        return {
            "success": True,
            "objectives": objectives
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.error(f"Response text: {response_text}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating concept learning objectives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate concept learning objectives: {str(e)}"
        )


# ============================================================================
# Interactive Simulation Generation Endpoints
# ============================================================================

class LearningOutcome(BaseModel):
    code: str
    text: str

class OutcomeConnection(BaseModel):
    code: str
    text: str
    clos: List[str]

class GenerateLearningOutcomesSimulationRequest(BaseModel):
    course_format: str  # "cohort" or "self-paced"
    module_number: int
    module_title: str
    module_outcomes: List[LearningOutcome]
    course_outcomes: List[LearningOutcome]

class GenerateSimulationRequest(BaseModel):
    simulation_type: str  # "learning-outcomes-map", "quiz", "simulator", etc.
    course_format: str = "cohort"  # "cohort" or "self-paced"
    data: dict

def generate_learning_outcomes_simulation_html(
    course_format: str,
    module_number: int,
    module_title: str,
    module_outcomes: List[dict],
    course_outcomes: List[dict]
) -> str:
    """
    Generate an interactive learning outcomes mapping simulation.

    Uses standardized design system with Geist typography and neutral color palette.
    """

    # Determine badge text and outcome codes based on course format
    if course_format == "self-paced":
        badge_text = f"MODULE {module_number}"
        outcome_prefix = "MLO"
        outcome_label = "module"
    else:  # cohort
        badge_text = f"WEEK {module_number}"
        outcome_prefix = "WLO"
        outcome_label = "week"

    # Build module outcomes list
    module_outcomes_js = "[\n"
    for i, outcome in enumerate(module_outcomes):
        module_outcomes_js += f"""        {{
            code: '{outcome_prefix} {module_number}.{i+1}',
            text: '{outcome["text"].replace("'", "\\'")}',
            clos: {json.dumps(outcome.get("clos", []))}
        }},\n"""
    module_outcomes_js += "    ]"

    # Build course outcomes list
    course_outcomes_js = "[\n"
    for outcome in course_outcomes:
        course_outcomes_js += f"""        {{
            code: '{outcome["code"]}',
            text: '{outcome["text"].replace("'", "\\'")}'
        }},\n"""
    course_outcomes_js += "    ]"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learning Outcomes - {module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --color-neutral-50: #fafafa;
            --color-neutral-100: #f5f5f5;
            --color-neutral-200: #e5e5e5;
            --color-neutral-300: #d4d4d4;
            --color-neutral-400: #a3a3a3;
            --color-neutral-500: #737373;
            --color-neutral-600: #525252;
            --color-neutral-700: #404040;
            --color-neutral-800: #262626;
            --color-neutral-900: #171717;
            --font-family-primary: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --border-radius: 8px;
            --border-radius-sm: 4px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-family-primary);
            background: white;
            color: var(--color-neutral-900);
            padding: 24px;
            line-height: 1.6;
        }}

        .outcomes-container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .header {{
            margin-bottom: 1.5rem;
        }}

        .header h3 {{
            color: var(--color-neutral-900);
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            color: var(--color-neutral-600);
            font-size: 0.9rem;
        }}

        .week-outcomes {{
            background: var(--color-neutral-50);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--border-radius);
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        }}

        .week-outcomes h4 {{
            color: var(--color-neutral-900);
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .week-badge {{
            background: var(--color-neutral-900);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: var(--border-radius-sm);
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .wlo-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .wlo-item {{
            background: white;
            border: 1px solid var(--color-neutral-200);
            border-radius: 6px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .wlo-item:hover {{
            border-color: var(--color-neutral-900);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .wlo-item:focus {{
            outline: 2px solid #3182ce;
            outline-offset: 2px;
        }}

        .wlo-item.active {{
            border-color: var(--color-neutral-900);
            border-width: 2px;
            background: var(--color-neutral-50);
        }}

        .wlo-header {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .wlo-code {{
            background: var(--color-neutral-900);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: var(--border-radius-sm);
            font-size: 0.75rem;
            font-weight: 600;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .wlo-text {{
            color: var(--color-neutral-700);
            font-size: 0.95rem;
            flex-grow: 1;
        }}

        .connection-indicator {{
            color: var(--color-neutral-600);
            font-size: 0.75rem;
            margin-top: 0.5rem;
            padding-left: calc(0.75rem + 0.5rem + 50px);
            display: none;
        }}

        .wlo-item.active .connection-indicator {{
            display: block;
        }}

        .course-outcomes {{
            background: white;
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--border-radius);
            padding: 1.25rem;
        }}

        .course-outcomes h4 {{
            color: var(--color-neutral-900);
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}

        .clo-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .clo-item {{
            background: var(--color-neutral-50);
            border: 1px solid var(--color-neutral-200);
            border-radius: 6px;
            padding: 1rem;
            opacity: 0.5;
            transition: all 0.3s ease;
        }}

        .clo-item.highlighted {{
            opacity: 1;
            border-color: var(--color-neutral-900);
            border-width: 2px;
            background: var(--color-neutral-100);
        }}

        .clo-header {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .clo-code {{
            background: var(--color-neutral-600);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: var(--border-radius-sm);
            font-size: 0.75rem;
            font-weight: 600;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .clo-item.highlighted .clo-code {{
            background: var(--color-neutral-900);
        }}

        .clo-text {{
            color: var(--color-neutral-700);
            font-size: 0.95rem;
        }}

        .help-text {{
            background: var(--color-neutral-50);
            border-left: 3px solid var(--color-neutral-900);
            padding: 0.75rem 1rem;
            margin-top: 1rem;
            border-radius: var(--border-radius-sm);
        }}

        .help-text p {{
            color: var(--color-neutral-900);
            font-size: 0.85rem;
        }}

        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }}

        .complete-button {{
            display: block;
            width: 100%;
            max-width: 300px;
            margin: 2rem auto 0;
            padding: 14px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .complete-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}

        .complete-button:active {{
            transform: translateY(0);
        }}

        @media (max-width: 640px) {{
            body {{
                padding: 16px;
            }}
            .wlo-header, .clo-header {{
                flex-direction: column;
                gap: 0.5rem;
            }}
            .week-outcomes, .course-outcomes {{
                padding: 1rem;
            }}
            .connection-indicator {{
                padding-left: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="outcomes-container">
        <div class="header">
            <h3>Learning Outcomes</h3>
            <p>Click any {outcome_label} outcome below to see how it connects to course-level goals</p>
        </div>

        <div class="week-outcomes">
            <h4>
                <span class="week-badge">{badge_text}</span>
                <span>{module_title}</span>
            </h4>
            <div class="wlo-list" role="list"></div>
        </div>

        <div class="course-outcomes">
            <h4>Course-Level Outcomes</h4>
            <div class="clo-list" role="list"></div>
        </div>

        <div class="help-text">
            <p><strong>How to use:</strong> Each {outcome_label} outcome contributes to broader course-level goals. Click outcomes above to explore the connections.</p>
        </div>

        <button id="complete-btn" class="complete-button" onclick="markComplete()">
            I've Reviewed the Outcomes →
        </button>
    </div>

    <script>
        const courseOutcomes = {course_outcomes_js};

        const wlos = {module_outcomes_js};

        const wloList = document.querySelector('.wlo-list');
        const cloList = document.querySelector('.clo-list');

        // Render WLOs/MLOs
        wlos.forEach(wlo => {{
            const div = document.createElement('div');
            div.className = 'wlo-item';
            div.setAttribute('tabindex', '0');
            div.setAttribute('role', 'button');
            div.innerHTML = `
                <div class="wlo-header">
                    <span class="wlo-code">${{wlo.code}}</span>
                    <span class="wlo-text">${{wlo.text}}</span>
                </div>
                <div class="connection-indicator">→ Contributes to: ${{wlo.clos.join(', ')}}</div>
            `;
            div.onclick = () => highlight(wlo.clos, div);
            div.onkeydown = (e) => {{
                if (e.key === 'Enter' || e.key === ' ') {{
                    e.preventDefault();
                    highlight(wlo.clos, div);
                }}
            }};
            wloList.appendChild(div);
        }});

        // Render CLOs
        courseOutcomes.forEach(clo => {{
            const div = document.createElement('div');
            div.className = 'clo-item';
            div.dataset.code = clo.code;
            div.innerHTML = `
                <div class="clo-header">
                    <span class="clo-code">${{clo.code}}</span>
                    <span class="clo-text">${{clo.text}}</span>
                </div>
            `;
            cloList.appendChild(div);
        }});

        const startTime = Date.now();
        let interactionCount = 0;
        const interactedOutcomes = new Set();

        function highlight(cloCodes, wloEl) {{
            const wasActive = wloEl.classList.contains('active');
            // Clear all highlights
            document.querySelectorAll('.wlo-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.clo-item').forEach(el => el.classList.remove('highlighted'));
            // If wasn't active, activate and highlight connected CLOs
            if (!wasActive) {{
                wloEl.classList.add('active');
                cloCodes.forEach(code => {{
                    const cloEl = document.querySelector(`[data-code="${{code}}"]`);
                    if (cloEl) cloEl.classList.add('highlighted');
                }});

                // Track interaction
                interactionCount++;
                const wloCode = wloEl.querySelector('.wlo-code').textContent;
                interactedOutcomes.add(wloCode);
            }}
        }}

        function markComplete() {{
            const duration = Date.now() - startTime;

            // Send completion data to parent window
            window.parent.postMessage({{
                type: 'simulation-complete',
                simulationType: 'learning-outcomes-map',
                data: {{
                    duration: duration,
                    completedAt: new Date().toISOString(),
                    interactionCount: interactionCount,
                    interactedOutcomes: Array.from(interactedOutcomes),
                    totalOutcomes: wlos.length
                }}
            }}, '*');

            // Visual feedback
            const btn = document.getElementById('complete-btn');
            btn.textContent = 'Review Complete! ✓';
            btn.style.background = '#10b981';
            btn.disabled = true;
        }}
    </script>
</body>
</html>"""

    return html_content


def generate_pre_assessment_quiz_html(
    module_title: str,
    questions: List[dict]
) -> str:
    """
    Generate a pre-assessment quiz simulation.

    Questions format: [{"question": "...", "options": ["A", "B", "C"], "info": "..."}]
    """

    questions_js = "[\n"
    for q in questions:
        questions_js += f"""        {{
            question: '{q["question"].replace("'", "\\'")}',
            options: {json.dumps(q.get("options", []))},
            info: '{q.get("info", "").replace("'", "\\'")}'
        }},\n"""
    questions_js += "    ]"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pre-Assessment: {module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --color-neutral-50: #fafafa;
            --color-neutral-100: #f5f5f5;
            --color-neutral-200: #e5e5e5;
            --color-neutral-300: #d4d4d4;
            --color-neutral-400: #a3a3a3;
            --color-neutral-500: #737373;
            --color-neutral-600: #525252;
            --color-neutral-700: #404040;
            --color-neutral-800: #262626;
            --color-neutral-900: #171717;
            --font-family-primary: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-family-primary);
            background: white;
            color: var(--color-neutral-900);
            padding: 24px;
            line-height: 1.6;
        }}

        .quiz-container {{
            max-width: 700px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid var(--color-neutral-200);
        }}

        .header h2 {{
            color: var(--color-neutral-900);
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            color: var(--color-neutral-600);
            font-size: 0.95rem;
        }}

        .question-card {{
            background: var(--color-neutral-50);
            border: 1px solid var(--color-neutral-200);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .question-number {{
            color: var(--color-neutral-600);
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .question-text {{
            color: var(--color-neutral-900);
            font-size: 1.05rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }}

        .options {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .option {{
            background: white;
            border: 2px solid var(--color-neutral-200);
            border-radius: 6px;
            padding: 0.75rem 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .option:hover {{
            border-color: var(--color-neutral-900);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .option:focus {{
            outline: 2px solid #3182ce;
            outline-offset: 2px;
        }}

        .option.selected {{
            background: var(--color-neutral-900);
            border-color: var(--color-neutral-900);
            color: white;
        }}

        .option-label {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid var(--color-neutral-400);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            flex-shrink: 0;
        }}

        .option.selected .option-label {{
            background: white;
            color: var(--color-neutral-900);
            border-color: white;
        }}

        .option-text {{
            flex-grow: 1;
        }}

        .info-box {{
            background: var(--color-neutral-100);
            border-left: 3px solid var(--color-neutral-900);
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 4px;
            display: none;
        }}

        .info-box.visible {{
            display: block;
            animation: slideIn 0.3s ease-out;
        }}

        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .info-box p {{
            color: var(--color-neutral-900);
            font-size: 0.9rem;
            margin: 0;
        }}

        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 2px solid var(--color-neutral-200);
        }}

        .footer p {{
            color: var(--color-neutral-600);
            font-size: 0.9rem;
        }}

        @media (max-width: 640px) {{
            body {{
                padding: 16px;
            }}
            .question-card {{
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="quiz-container">
        <div class="header">
            <h2>Pre-Assessment: {module_title}</h2>
            <p>Gauge your current understanding (no right or wrong answers)</p>
        </div>

        <div id="questions-container"></div>

        <div class="footer">
            <p><strong>Self-reflection:</strong> Use your responses to identify areas for focused learning</p>
        </div>
    </div>

    <script>
        const questions = {questions_js};
        const responses = new Array(questions.length).fill(null);
        let startTime = Date.now();

        const container = document.getElementById('questions-container');

        questions.forEach((q, index) => {{
            const card = document.createElement('div');
            card.className = 'question-card';
            card.setAttribute('data-question-index', index);

            const questionNumber = document.createElement('div');
            questionNumber.className = 'question-number';
            questionNumber.textContent = `Question ${{index + 1}} of ${{questions.length}}`;

            const questionText = document.createElement('div');
            questionText.className = 'question-text';
            questionText.textContent = q.question;

            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options';

            q.options.forEach((opt, optIndex) => {{
                const option = document.createElement('div');
                option.className = 'option';
                option.setAttribute('tabindex', '0');
                option.setAttribute('role', 'button');
                option.setAttribute('data-option-index', optIndex);
                option.setAttribute('data-option-value', opt);

                const label = document.createElement('div');
                label.className = 'option-label';
                label.textContent = String.fromCharCode(65 + optIndex); // A, B, C, D

                const text = document.createElement('div');
                text.className = 'option-text';
                text.textContent = opt;

                option.appendChild(label);
                option.appendChild(text);

                option.onclick = () => selectOption(card, option, index, optIndex, opt);
                option.onkeydown = (e) => {{
                    if (e.key === 'Enter' || e.key === ' ') {{
                        e.preventDefault();
                        selectOption(card, option, index, optIndex, opt);
                    }}
                }};

                optionsDiv.appendChild(option);
            }});

            const infoBox = document.createElement('div');
            infoBox.className = 'info-box';
            const infoText = document.createElement('p');
            infoText.textContent = q.info;
            infoBox.appendChild(infoText);

            card.appendChild(questionNumber);
            card.appendChild(questionText);
            card.appendChild(optionsDiv);
            card.appendChild(infoBox);

            container.appendChild(card);
        }});

        // Add complete button
        const completeBtn = document.createElement('button');
        completeBtn.id = 'complete-btn';
        completeBtn.textContent = 'Complete Pre-Assessment';
        completeBtn.style.cssText = `
            display: block;
            margin: 2rem auto 0;
            padding: 14px 32px;
            background: var(--color-neutral-900);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            opacity: 0.5;
            pointer-events: none;
        `;
        completeBtn.onclick = submitAssessment;
        container.parentElement.insertBefore(completeBtn, container.parentElement.querySelector('.footer'));

        function selectOption(card, selectedOption, questionIndex, optionIndex, optionValue) {{
            // Remove selected class from all options in this card
            card.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
            // Add selected class to clicked option
            selectedOption.classList.add('selected');
            // Show info box
            const infoBox = card.querySelector('.info-box');
            infoBox.classList.add('visible');

            // Store response
            responses[questionIndex] = {{
                question: questions[questionIndex].question,
                selectedOption: optionValue,
                selectedIndex: optionIndex,
                timestamp: Date.now()
            }};

            // Enable complete button if all questions answered
            const allAnswered = responses.every(r => r !== null);
            const btn = document.getElementById('complete-btn');
            if (allAnswered) {{
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
            }}
        }}

        function submitAssessment() {{
            const duration = Date.now() - startTime;

            // Send results to parent window via postMessage
            window.parent.postMessage({{
                type: 'simulation-complete',
                simulationType: 'pre-assessment-quiz',
                data: {{
                    responses: responses,
                    duration: duration,
                    completedAt: new Date().toISOString(),
                    questionsCount: questions.length
                }}
            }}, '*');

            // Visual feedback
            const btn = document.getElementById('complete-btn');
            btn.textContent = 'Submitted! ✓';
            btn.style.background = '#10b981';
            btn.disabled = true;
        }}
    </script>
</body>
</html>"""

    return html_content


def generate_concept_preview_html(
    module_title: str,
    key_points: List[str],
    learning_objectives: List[str]
) -> str:
    """
    Generate a concept preview/overview simulation.
    """

    points_html = ""
    for point in key_points:
        points_html += f"""
            <div class="point-item">
                <div class="point-icon">▸</div>
                <div class="point-text">{point}</div>
            </div>"""

    objectives_html = ""
    for i, obj in enumerate(learning_objectives, 1):
        objectives_html += f"""
            <div class="objective-item">
                <div class="objective-number">{i}</div>
                <div class="objective-text">{obj}</div>
            </div>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview: {module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --color-neutral-50: #fafafa;
            --color-neutral-100: #f5f5f5;
            --color-neutral-200: #e5e5e5;
            --color-neutral-600: #525252;
            --color-neutral-700: #404040;
            --color-neutral-900: #171717;
            --font-family-primary: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-family-primary);
            background: white;
            color: var(--color-neutral-900);
            padding: 24px;
            line-height: 1.6;
        }}

        .preview-container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2.5rem;
        }}

        .header h2 {{
            color: var(--color-neutral-900);
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }}

        .header p {{
            color: var(--color-neutral-600);
            font-size: 1.05rem;
        }}

        .section {{
            background: var(--color-neutral-50);
            border: 1px solid var(--color-neutral-200);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .section h3 {{
            color: var(--color-neutral-900);
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
        }}

        .point-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: white;
            border-radius: 6px;
        }}

        .point-icon {{
            color: var(--color-neutral-900);
            font-size: 1.25rem;
            flex-shrink: 0;
        }}

        .point-text {{
            color: var(--color-neutral-700);
            font-size: 0.95rem;
        }}

        .objective-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: white;
            border-radius: 6px;
        }}

        .objective-number {{
            width: 32px;
            height: 32px;
            background: var(--color-neutral-900);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }}

        .objective-text {{
            color: var(--color-neutral-700);
            font-size: 0.95rem;
            padding-top: 0.25rem;
        }}

        .complete-button {{
            display: block;
            width: 100%;
            max-width: 300px;
            margin: 2rem auto 0;
            padding: 14px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .complete-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}

        .complete-button:active {{
            transform: translateY(0);
        }}

        @media (max-width: 640px) {{
            body {{
                padding: 16px;
            }}
            .header h2 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="header">
            <h2>{module_title}</h2>
            <p>What you'll learn in this module</p>
        </div>

        <div class="section">
            <h3>Key Concepts</h3>
            {points_html}
        </div>

        <div class="section">
            <h3>Learning Objectives</h3>
            {objectives_html}
        </div>

        <button id="complete-btn" class="complete-button" onclick="markComplete()">
            I've Reviewed This →
        </button>
    </div>

    <script>
        const startTime = Date.now();

        function markComplete() {{
            const duration = Date.now() - startTime;

            // Send completion data to parent window
            window.parent.postMessage({{
                type: 'simulation-complete',
                simulationType: 'concept-preview',
                data: {{
                    duration: duration,
                    completedAt: new Date().toISOString(),
                    moduleTitle: '{module_title}'
                }}
            }}, '*');

            // Visual feedback
            const btn = document.getElementById('complete-btn');
            btn.textContent = 'Review Recorded! ✓';
            btn.style.background = '#10b981';
            btn.disabled = true;
        }}
    </script>
</body>
</html>"""

    return html_content

@app.post("/generate-simulation")
async def generate_simulation(body: GenerateSimulationRequest):
    """
    Generate an interactive educational simulation.

    Args:
        simulation_type: Type of simulation to generate
        course_format: "cohort" or "self-paced" (affects terminology)
        data: Simulation-specific data

    Returns:
        Generated HTML simulation with metadata
    """
    try:
        if body.simulation_type == "learning-outcomes-map":
            # Extract data
            module_number = body.data.get("module_number", 1)
            module_title = body.data.get("module_title", "Module")
            module_outcomes = body.data.get("module_outcomes", [])
            course_outcomes = body.data.get("course_outcomes", [])

            # Generate HTML
            html = generate_learning_outcomes_simulation_html(
                course_format=body.course_format,
                module_number=module_number,
                module_title=module_title,
                module_outcomes=module_outcomes,
                course_outcomes=course_outcomes
            )

            outcome_type = "MLO" if body.course_format == "self-paced" else "WLO"

            logger.info(f"Generated learning outcomes simulation for {module_title} ({body.course_format} format)")

            return {
                "success": True,
                "html": html,
                "metadata": {
                    "type": "learning-outcomes-map",
                    "title": f"{module_title} Learning Outcomes",
                    "course_format": body.course_format,
                    "outcome_type": outcome_type,
                    "accessibility_compliant": True,
                    "design_system_version": "1.0"
                }
            }

        elif body.simulation_type == "pre-assessment-quiz":
            # Extract data
            module_title = body.data.get("module_title", "Module")
            questions = body.data.get("questions", [])

            # Generate HTML
            html = generate_pre_assessment_quiz_html(
                module_title=module_title,
                questions=questions
            )

            logger.info(f"Generated pre-assessment quiz for {module_title}")

            return {
                "success": True,
                "html": html,
                "metadata": {
                    "type": "pre-assessment-quiz",
                    "title": f"{module_title} Pre-Assessment",
                    "question_count": len(questions),
                    "accessibility_compliant": True,
                    "design_system_version": "1.0"
                }
            }

        elif body.simulation_type == "concept-preview":
            # Extract data
            module_title = body.data.get("module_title", "Module")
            key_points = body.data.get("key_points", [])
            learning_objectives = body.data.get("learning_objectives", [])

            # Generate HTML
            html = generate_concept_preview_html(
                module_title=module_title,
                key_points=key_points,
                learning_objectives=learning_objectives
            )

            logger.info(f"Generated concept preview for {module_title}")

            return {
                "success": True,
                "html": html,
                "metadata": {
                    "type": "concept-preview",
                    "title": f"{module_title} Preview",
                    "accessibility_compliant": True,
                    "design_system_version": "1.0"
                }
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Simulation type '{body.simulation_type}' not yet implemented"
            )

    except Exception as e:
        logger.error(f"Error generating simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate simulation: {str(e)}"
        )


@app.post("/courses/{course_id}/modules/{module_id}/cache-simulations")
async def cache_module_simulations(course_id: str, module_id: str):
    """
    Generate and cache all three simulations for a module.

    Creates simulations directory structure and saves HTML files:
    - pre-assessment-quiz.html
    - concept-preview.html
    - learning-outcomes-map.html
    """
    try:
        # Get module metadata
        module_dir = config.RESOURCE_BANK_DIR / "user-courses" / course_id / module_id
        if not module_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found in course {course_id}"
            )

        metadata_file = module_dir / "metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            module_data = json.load(f)

        # Get course metadata for course-level outcomes
        course_metadata_file = config.RESOURCE_BANK_DIR / "user-courses" / course_id / "metadata.json"
        with open(course_metadata_file, 'r', encoding='utf-8') as f:
            course_data = json.load(f)

        # Create simulations directory
        simulations_dir = module_dir / "simulations"
        simulations_dir.mkdir(exist_ok=True)

        module_outcomes = module_data.get("module_learning_outcomes", [])
        module_title = module_data.get("title", module_id)
        course_outcomes = course_data.get("course_learning_outcomes", [])
        course_format = course_data.get("format", "cohort")  # Default to cohort if not specified

        # Generate each simulation type
        generated = {}

        # 1. Pre-Assessment Quiz
        quiz_data = {
            "module_title": module_title,
            "questions": [
                {
                    "question": f"How familiar are you with: {outcome}?",
                    "options": ["Not familiar", "Somewhat familiar", "Very familiar", "Expert level"],
                    "info": "This helps us personalize your learning experience"
                }
                for outcome in module_outcomes[:3]  # Use first 3 outcomes
            ]
        }
        quiz_html = generate_pre_assessment_quiz_html(
            module_title=quiz_data["module_title"],
            questions=quiz_data["questions"]
        )
        quiz_file = simulations_dir / "pre-assessment-quiz.html"
        quiz_file.write_text(quiz_html, encoding='utf-8')
        generated["pre-assessment-quiz"] = str(quiz_file.relative_to(config.RESOURCE_BANK_DIR))

        # 2. Concept Preview
        preview_data = {
            "module_title": module_title,
            "key_points": [outcome.replace("Students will be able to ", "").replace("students will be able to ", "")
                          for outcome in module_outcomes[:4]],
            "learning_objectives": module_outcomes
        }
        preview_html = generate_concept_preview_html(
            module_title=preview_data["module_title"],
            key_points=preview_data["key_points"],
            learning_objectives=preview_data["learning_objectives"]
        )
        preview_file = simulations_dir / "concept-preview.html"
        preview_file.write_text(preview_html, encoding='utf-8')
        generated["concept-preview"] = str(preview_file.relative_to(config.RESOURCE_BANK_DIR))

        # 3. Learning Outcomes Map
        map_data = {
            "module_number": int(module_id.split("-")[1]) if "-" in module_id else 1,
            "module_title": module_title,
            "module_outcomes": [
                {
                    "text": outcome,
                    "clos": [f"CLO {i+1}" for i in range(min(2, len(course_outcomes)))]  # Map to first 2 CLOs
                }
                for outcome in module_outcomes
            ],
            "course_outcomes": [
                {"code": f"CLO {i+1}", "text": outcome}
                for i, outcome in enumerate(course_outcomes)
            ]
        }
        map_html = generate_learning_outcomes_simulation_html(
            course_format=course_format,
            module_number=map_data["module_number"],
            module_title=map_data["module_title"],
            module_outcomes=map_data["module_outcomes"],
            course_outcomes=map_data["course_outcomes"]
        )
        map_file = simulations_dir / "learning-outcomes-map.html"
        map_file.write_text(map_html, encoding='utf-8')
        generated["learning-outcomes-map"] = str(map_file.relative_to(config.RESOURCE_BANK_DIR))

        logger.info(f"Cached {len(generated)} simulations for {course_id}/{module_id}")

        return {
            "success": True,
            "module_id": module_id,
            "course_id": course_id,
            "simulations": generated,
            "cached_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error caching simulations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cache simulations: {str(e)}"
        )


@app.get("/courses/{course_id}/modules/{module_id}/simulations/{simulation_type}")
async def get_cached_simulation(course_id: str, module_id: str, simulation_type: str):
    """
    Serve a cached simulation HTML file.

    Args:
        course_id: Course identifier
        module_id: Module identifier
        simulation_type: One of: pre-assessment-quiz, concept-preview, learning-outcomes-map
    """
    try:
        valid_types = ["pre-assessment-quiz", "concept-preview", "learning-outcomes-map"]
        if simulation_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid simulation type. Must be one of: {', '.join(valid_types)}"
            )

        simulation_file = (
            config.RESOURCE_BANK_DIR / "user-courses" / course_id / module_id /
            "simulations" / f"{simulation_type}.html"
        )

        if not simulation_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation not found. Generate it first using POST /courses/{course_id}/modules/{module_id}/cache-simulations"
            )

        html_content = simulation_file.read_text(encoding='utf-8')

        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving cached simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve simulation: {str(e)}"
        )


@app.post("/simulation-results")
async def save_simulation_results(request: Request):
    """
    Save simulation results to learner model and generate feedback.

    Expected payload:
    {
        "learner_id": "string",
        "course_id": "string",
        "module_id": "string",
        "simulation_type": "pre-assessment-quiz" | "concept-preview" | "learning-outcomes-map",
        "data": {...},
        "timestamp": "ISO 8601 string"
    }
    """
    try:
        payload = await request.json()
        learner_id = payload.get("learner_id")
        course_id = payload.get("course_id")
        module_id = payload.get("module_id")
        simulation_type = payload.get("simulation_type")
        data = payload.get("data")
        timestamp = payload.get("timestamp")

        if not all([learner_id, course_id, module_id, simulation_type, data]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )

        # Load learner model
        learner_model = load_learner_model(learner_id)

        # Initialize simulation_results structure if it doesn't exist
        if "simulation_results" not in learner_model:
            learner_model["simulation_results"] = {}

        # Store the simulation results
        if course_id not in learner_model["simulation_results"]:
            learner_model["simulation_results"][course_id] = {}

        if module_id not in learner_model["simulation_results"][course_id]:
            learner_model["simulation_results"][course_id][module_id] = []

        # Add this simulation result
        learner_model["simulation_results"][course_id][module_id].append({
            "simulation_type": simulation_type,
            "data": data,
            "timestamp": timestamp
        })

        # Save updated learner model
        save_learner_model(learner_id, learner_model)
        logger.info(f"Saved simulation results for {learner_id}: {simulation_type}")

        # Generate feedback based on simulation type and results
        feedback = generate_simulation_feedback(
            simulation_type=simulation_type,
            data=data,
            learner_model=learner_model,
            course_id=course_id,
            module_id=module_id
        )

        return {
            "success": True,
            "message": "Simulation results saved successfully",
            "feedback": feedback
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving simulation results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save simulation results: {str(e)}"
        )


def generate_simulation_feedback(
    simulation_type: str,
    data: dict,
    learner_model: dict,
    course_id: str,
    module_id: str
) -> dict:
    """
    Generate personalized feedback based on simulation results.

    Args:
        simulation_type: Type of simulation completed
        data: Simulation response data
        learner_model: Current learner model
        course_id: Course identifier
        module_id: Module identifier

    Returns:
        Feedback dictionary with title, message, and insights
    """
    try:
        if simulation_type == "pre-assessment-quiz":
            # Analyze pre-assessment responses
            responses = data.get("responses", [])
            questions_count = data.get("questionsCount", len(responses))
            duration = data.get("duration", 0)

            # Count responses by option value (if available)
            confidence_levels = {"high": 0, "medium": 0, "low": 0, "none": 0}
            for response in responses:
                option = response.get("selectedOption", "").lower()
                if "very confident" in option or "mastered" in option:
                    confidence_levels["high"] += 1
                elif "somewhat confident" in option or "familiar" in option:
                    confidence_levels["medium"] += 1
                elif "not confident" in option or "heard of" in option:
                    confidence_levels["low"] += 1
                elif "never heard" in option or "no idea" in option:
                    confidence_levels["none"] += 1

            # Generate insights based on confidence distribution
            insights = []

            if confidence_levels["high"] >= questions_count * 0.5:
                insights.append("You seem to have strong prior knowledge in several areas - we'll move quickly through familiar content.")
            elif confidence_levels["none"] + confidence_levels["low"] >= questions_count * 0.5:
                insights.append("We'll take extra time to build foundations in these new concepts.")
            else:
                insights.append("You have a mix of familiarity - perfect for adaptive learning!")

            if duration < 30000:  # Less than 30 seconds
                insights.append("You completed this quickly - we'll ensure the pace matches your needs.")

            insights.append("Your responses will help personalize upcoming lessons and examples.")

            return {
                "title": "Pre-Assessment Complete!",
                "message": f"Thank you for completing the pre-assessment. Your responses to {questions_count} questions will help us tailor your learning experience.",
                "insights": insights
            }

        elif simulation_type == "concept-preview":
            return {
                "title": "Preview Explored!",
                "message": "Great job exploring the concept preview. This should give you a solid foundation for what's coming next.",
                "insights": [
                    "These preview concepts will be revisited in detail during the lesson.",
                    "Feel free to refer back to this preview anytime."
                ]
            }

        elif simulation_type == "learning-outcomes-map":
            return {
                "title": "Learning Path Reviewed!",
                "message": "You've reviewed the learning outcomes map. Keep these goals in mind as you progress.",
                "insights": [
                    "Each outcome builds on previous concepts.",
                    "You can revisit this map anytime to track your progress."
                ]
            }

        else:
            return {
                "title": "Simulation Complete!",
                "message": "Thank you for completing this interactive simulation.",
                "insights": []
            }

    except Exception as e:
        logger.error(f"Error generating simulation feedback: {e}")
        return {
            "title": "Simulation Complete!",
            "message": "Thank you for completing this simulation.",
            "insights": []
        }


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/admin/learners")
async def get_all_learners(course_id: str = None):
    """
    Get all learners with their basic progress information.

    Args:
        course_id: Optional course ID to filter learners by current course

    Returns a list of all learners with basic stats for admin dashboard.
    """
    try:
        learners_data = []

        # Iterate through all learner model files
        for learner_file in config.LEARNER_MODELS_DIR.glob("*.json"):
            learner_id = learner_file.stem

            try:
                learner_model = load_learner_model(learner_id)

                # Filter by course if specified
                if course_id and learner_model.get("current_course") != course_id:
                    continue

                # Build learner summary
                learner_summary = {
                    "learner_id": learner_id,
                    "learner_name": learner_model.get("learner_name", learner_id),
                    "current_course": learner_model.get("current_course"),
                    "progress": {
                        "current_concept": learner_model.get("current_concept"),
                        "completed_concepts": learner_model.get("completed_concepts", []),
                        "overall_progress": learner_model.get("overall_progress", {})
                    }
                }

                learners_data.append(learner_summary)

            except Exception as e:
                logger.warning(f"Failed to load learner {learner_id}: {e}")
                continue

        logger.info(f"Retrieved {len(learners_data)} learners{f' for course {course_id}' if course_id else ''}")

        return {
            "success": True,
            "learners": learners_data,
            "total": len(learners_data)
        }

    except Exception as e:
        logger.error(f"Error getting all learners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve learners: {str(e)}"
        )


class UpdateModuleRequest(BaseModel):
    course_id: str
    title: str
    module_learning_outcomes: List[str]


@app.put("/admin/modules/{module_id}")
async def update_module(module_id: str, body: UpdateModuleRequest):
    """
    Update module metadata.

    Args:
        module_id: Module identifier
        body: Updated module data

    Returns success status and updated module data.
    """
    try:
        module_dir = config.get_module_dir(module_id, body.course_id)

        if not module_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found in course {body.course_id}"
            )

        metadata_file = module_dir / "metadata.json"

        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            metadata = {"id": module_id}

        # Update fields
        metadata["title"] = body.title
        metadata["module_learning_outcomes"] = body.module_learning_outcomes

        # Save updated metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Updated module {module_id} in course {body.course_id}")

        return {
            "success": True,
            "module_id": module_id,
            "title": body.title,
            "module_learning_outcomes": body.module_learning_outcomes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating module {module_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update module: {str(e)}"
        )


class UpdateConceptRequest(BaseModel):
    course_id: str
    module_id: str
    title: str
    learning_objectives: List[str]


@app.put("/admin/concepts/{concept_id}")
async def update_concept(concept_id: str, body: UpdateConceptRequest):
    """
    Update concept metadata.

    Args:
        concept_id: Concept identifier
        body: Updated concept data

    Returns success status and updated concept data.
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, body.course_id, body.module_id)

        if not concept_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept {concept_id} not found"
            )

        metadata_file = concept_dir / "metadata.json"

        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            metadata = {"concept_id": concept_id}

        # Update fields
        metadata["title"] = body.title
        metadata["learning_objectives"] = body.learning_objectives

        # Save updated metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Updated concept {concept_id} in course {body.course_id}")

        return {
            "success": True,
            "concept_id": concept_id,
            "title": body.title,
            "learning_objectives": body.learning_objectives
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating concept {concept_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update concept: {str(e)}"
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


