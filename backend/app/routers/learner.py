from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional, Dict, Any
import logging
import os

from .. import config
from ..schemas import (
    StartRequest,
    ProgressResponse,
    HealthResponse
)
from ..tools import (
    create_learner_model,
    load_learner_model,
    save_learner_model,
    calculate_overall_calibration
)

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/start", status_code=status.HTTP_201_CREATED)
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

@router.get("/progress/{learner_id}", response_model=ProgressResponse)
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

@router.get("/learner/{learner_id}")
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

@router.put("/learner/{learner_id}/learning-style")
async def update_learning_style(learner_id: str, body: dict):
    """
    Update the learner's learning style preference.

    This allows learners to change their preferred content format
    (narrative, varied, adaptive) after experiencing the initial choice.
    """
    try:
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

@router.put("/learner/{learner_id}/practice-mode")
async def toggle_practice_mode(learner_id: str, body: dict):
    """
    Toggle practice mode for the learner.

    Practice mode allows learners to explore questions without affecting their mastery score.
    This provides choice and agency - learners can practice stress-free or work toward mastery.
    """
    try:
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
