"""
API Routers for Learner-related endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging


from ..schemas import (
    StartRequest,
    ChatRequest,
    ChatResponse,
    ProgressResponse,
    MasteryResponse,
    SubmitResponseRequest,
    EvaluationResponse,
)
from ..auth import get_current_user, validate_learner_exists
from ..agent import chat, generate_content
from ..tools import create_learner_model, load_learner_model, calculate_mastery, get_due_reviews, get_review_stats
from ..config import config


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def start_learner(request: Request, body: StartRequest):
    """
    Initialize a new learner.
    """
    try:
        logger.info(f"📝 Creating new learner: {body.learner_id}")
        learner_model = create_learner_model(
            body.learner_id,
            learner_name=body.learner_name,
            profile=body.profile
        )
        # Assuming database storage now, so no file to check
        logger.info(f"✅ Learner model created in db for: {body.learner_id}")
        return {
            "success": True,
            "learner_id": body.learner_id,
            "current_concept": learner_model["current_concept"],
            "message": "Learner initialized successfully. Ready to begin learning!"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error starting learner {body.learner_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initialize learner: {str(e)}")


@router.get("/progress/{learner_id}", response_model=ProgressResponse)
async def get_progress(learner_id: str = Depends(validate_learner_exists)):
    """
    Get learner's progress information.
    """
    try:
        model = load_learner_model(learner_id)
        all_confidence = []
        for concept_data in model["concepts"].values():
            all_confidence.extend(concept_data.get("confidence_history", []))
        overall_calibration = None
        if all_confidence:
            from ..confidence import calculate_overall_calibration
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
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get progress: {str(e)}")


@router.get("/mastery/{learner_id}/{concept_id}", response_model=MasteryResponse)
async def get_mastery(concept_id: str, learner_id: str = Depends(validate_learner_exists)):
    """
    Get mastery information for a specific concept.
    """
    try:
        mastery_info = calculate_mastery(learner_id, concept_id)
        return mastery_info
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating mastery: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to calculate mastery: {str(e)}")


@router.get("/learner/{learner_id}")
async def get_learner_model(learner_id: str = Depends(validate_learner_exists)):
    """
    Get the complete learner model.
    """
    model = load_learner_model(learner_id)
    return {"success": True, "learner_model": model}


@router.put("/learner/{learner_id}/learning-style")
async def update_learning_style(body: dict, learner_id: str = Depends(validate_learner_exists)):
    """
    Update the learner's learning style preference.
    """
    from ..tools import save_learner_model
    valid_styles = ["narrative", "varied", "adaptive"]
    new_style = body.get("learningStyle")
    if not new_style or new_style not in valid_styles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid learning style")
    model = load_learner_model(learner_id)
    if "profile" not in model:
        model["profile"] = {}
    old_style = model["profile"].get("learningStyle", "unknown")
    model["profile"]["learningStyle"] = new_style
    save_learner_model(learner_id, model)
    logger.info(f"✅ Updated learning style for {learner_id}: {old_style} → {new_style}")
    return {"success": True, "message": f"Learning style updated to '{new_style}'"}


@router.post("/submit-response", response_model=EvaluationResponse)
@limiter.limit("60/minute")
async def submit_response(request: Request, body: SubmitResponseRequest):
    """
    Evaluate a learner's response and generate adaptive next content.
    """
    try:
        from ..agent import evaluate_dialogue_response
        from ..tools import record_assessment_and_check_completion, save_learner_model
        from datetime import datetime

        is_correct = False
        dialogue_feedback = None

        if body.question_type == "multiple-choice":
            is_correct = body.user_answer == body.correct_answer
        elif body.question_type == "fill-blank":
            user_answer_normalized = body.user_answer.lower().strip()
            if isinstance(body.correct_answer, list):
                is_correct = any(user_answer_normalized == acceptable.lower().strip() for acceptable in body.correct_answer)
            else:
                is_correct = user_answer_normalized == body.correct_answer.lower().strip()
        elif body.question_type == "dialogue":
            evaluation = evaluate_dialogue_response(
                question=body.question_text,
                context=body.scenario_text or "",
                student_answer=body.user_answer,
                concept_id=body.current_concept
            )
            is_correct = evaluation.get("is_correct", False)
            dialogue_feedback = evaluation.get("feedback", "")

        # Determine calibration type and next content stage
        if body.confidence is None:
            calibration_type = None
            stage = "practice" if is_correct else "remediate"
            remediation_type = None if is_correct else "supportive"
        else:
            high_confidence = body.confidence >= 3
            if is_correct and high_confidence:
                calibration_type, stage, remediation_type = "calibrated", "practice", None
            elif is_correct and not high_confidence:
                calibration_type, stage, remediation_type = "underconfident", "reinforce", "brief"
            elif not is_correct and high_confidence:
                calibration_type, stage, remediation_type = "overconfident", "remediate", "full_calibration"
            else:
                calibration_type, stage, remediation_type = "calibrated_low", "remediate", "supportive"

        completion_result = record_assessment_and_check_completion(
            learner_id=body.learner_id,
            concept_id=body.current_concept,
            is_correct=is_correct,
            confidence=body.confidence,
            question_type=body.question_type
        )

        question_context = {
            "scenario": body.scenario_text or "",
            "question": body.question_text or "",
            "user_answer": body.user_answer,
            "correct_answer": body.correct_answer,
            "options": body.options or []
        } if stage in ["remediate", "reinforce"] else None

        result = generate_content(
            body.learner_id,
            stage,
            correctness=is_correct,
            confidence=body.confidence,
            remediation_type=remediation_type,
            question_context=question_context
        )

        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate next content")

        # Create feedback message
        feedback_messages = {
            "calibrated": "Well done! You knew it and got it right.",
            "underconfident": "You got it right! You know more than you think.",
            "overconfident": "Not quite - let's clarify this concept.",
            "calibrated_low": "You weren't sure, and this is tricky. Let's work through it."
        }
        feedback_text = dialogue_feedback or feedback_messages.get(calibration_type, "Thank you for your response.")

        correct_answer_display = body.correct_answer
        if body.question_type == "multiple-choice" and body.options and isinstance(body.correct_answer, int):
            if 0 <= body.correct_answer < len(body.options):
                correct_answer_display = body.options[body.correct_answer]

        assessment_result = {
            "type": "assessment-result",
            "score": 1.0 if is_correct else 0.0,
            "feedback": feedback_text,
            "correctAnswer": correct_answer_display if body.question_type != "dialogue" else None,
            "calibration": calibration_type,
            "languageConnection": None,
            "_next_content": result["content"],
        }

        return {
            "is_correct": is_correct,
            "confidence": body.confidence,
            "calibration_type": calibration_type,
            "feedback_message": feedback_text,
            "mastery_score": completion_result["mastery_score"],
            "mastery_threshold": config.MASTERY_THRESHOLD,
            "assessments_count": completion_result["assessments_count"],
            "concept_completed": completion_result["concept_completed"],
            "next_content": assessment_result,
        }
    except Exception as e:
        logger.error(f"Error evaluating response: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to evaluate response: {str(e)}")


@router.post("/generate-content")
@limiter.limit("60/minute")
async def generate_content_endpoint(request: Request, learner_id: str, stage: str = "start"):
    """
    Generate personalized learning content using AI.
    """
    result = generate_content(learner_id, stage)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Content generation failed"))
    return result


@router.get("/reviews/{learner_id}")
async def get_due_concepts(learner_id: str = Depends(validate_learner_exists), include_upcoming: int = 0):
    """
    Get concepts that are due for spaced repetition review.
    """
    model = load_learner_model(learner_id)
    due_concepts = get_due_reviews(model, include_upcoming=include_upcoming)
    return {"success": True, "due_concepts": due_concepts}


@router.get("/review-stats/{learner_id}")
async def get_review_statistics(learner_id: str = Depends(validate_learner_exists)):
    """
    Get overall statistics about spaced repetition progress.
    """
    model = load_learner_model(learner_id)
    stats = get_review_stats(model)
    return {"success": True, **stats}
