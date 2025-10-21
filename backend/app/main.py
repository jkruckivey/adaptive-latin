"""
FastAPI Application for Latin Adaptive Learning System

Main application with REST API endpoints for the adaptive learning tutor.
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .config import config
from .agent import chat
from .tools import (
    create_learner_model,
    load_learner_model,
    load_concept_metadata,
    calculate_mastery,
    list_all_concepts
)
from .confidence import calculate_overall_calibration

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
        learner_model = create_learner_model(request.learner_id)
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
