from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .. import config
from ..schemas import (
    ConceptResponse,
    MasteryResponse,
    SubmitResponseRequest,
    EvaluationResponse,
    DialogueEvaluationRequest,
    DialogueEvaluationResponse
)
from ..tools import (
    load_concept_metadata,
    load_learner_model,
    save_learner_model,
    calculate_mastery,
    list_all_concepts,
    record_assessment_and_check_completion,
    detect_struggle,
    detect_celebration_milestones
)
from ..agent import generate_content, call_anthropic_with_retry
from ..content_generators import generate_hint_request
from ..constants import (
    HINTS_ENABLED_IN_PRACTICE,
    HINTS_ENABLED_IN_GRADED,
    HINT_LEVEL_GENTLE,
    HINT_LEVEL_DIRECT,
    HINT_LEVEL_ANSWER
)

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)
limiter = None # Will be injected

@router.get("/concept/{concept_id}", response_model=ConceptResponse)
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

        # Convert difficulty to string if it's an integer
        difficulty = metadata.get("difficulty", "medium")
        if isinstance(difficulty, int):
            difficulty = str(difficulty)

        return {
            "concept_id": metadata.get("concept_id", concept_id),
            "title": metadata.get("title", concept_id),
            "difficulty": difficulty,
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

@router.get("/mastery/{learner_id}/{concept_id}", response_model=MasteryResponse)
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

@router.get("/concepts")
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

@router.post("/generate-content")
async def generate_content_endpoint(request: Request, learner_id: str, stage: str = "start"):
    """
    Generate personalized learning content using AI.

    Uses learner profile to create customized lessons, examples, and assessments.
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

@router.post("/submit-response", response_model=EvaluationResponse)
async def submit_response(request: Request, body: SubmitResponseRequest):
    """
    Evaluate a learner's response and generate adaptive next content.
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
            from ..agent import evaluate_dialogue_response

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

        # For dialogue questions, use the AI-generated score; for others, use binary correct/incorrect
        result_score = dialogue_score if body.question_type == "dialogue" else (1.0 if is_correct else 0.0)

        assessment_result = {
            "type": "assessment-result",
            "score": result_score,
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


@router.post("/evaluate-dialogue", response_model=DialogueEvaluationResponse)
async def evaluate_dialogue(body: DialogueEvaluationRequest):
    """
    Evaluate a dialogue response for multi-turn conversations.

    This is a lightweight endpoint specifically for conversational dialogue
    that returns feedback and follow-up questions without generating new content.
    """
    try:
        from ..agent import evaluate_dialogue_response

        logger.info(f"Evaluating dialogue for learner {body.learner_id}, exchange #{body.exchange_count + 1}")

        evaluation = evaluate_dialogue_response(
            question=body.question,
            context=body.context or "",
            student_answer=body.answer,
            concept_id=body.concept_id,
            exchange_count=body.exchange_count
        )

        logger.info(f"Dialogue evaluation result: score={evaluation.get('score')}, complete={evaluation.get('dialogueComplete')}")

        return {
            "isCorrect": evaluation.get("is_correct", False),
            "feedback": evaluation.get("feedback", "Thank you for your response."),
            "score": evaluation.get("score", 0.5),
            "followUpQuestion": evaluation.get("followUpQuestion", ""),
            "dialogueComplete": evaluation.get("dialogueComplete", False)
        }

    except Exception as e:
        logger.error(f"Error evaluating dialogue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate dialogue: {str(e)}"
        )


@router.post("/request-hint")
async def request_hint(request: Request, body: dict):
    """
    Generate a hint for the current question (practice mode only).
    """
    try:
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
        response = call_anthropic_with_retry(
            system_prompt="You are a patient Latin tutor providing hints to a struggling student in practice mode. Be encouraging and educational.",
            user_message=hint_prompt,
            # model=config.CLAUDE_MODEL, # call_anthropic_with_retry uses config.ANTHROPIC_MODEL internally
            # max_tokens=500  # call_anthropic_with_retry uses fixed max_tokens or we need to update it to accept kwargs if needed.
            # Checking agent.py definition: def call_anthropic_with_retry(system_prompt: str, user_message: str, max_retries: int = DEFAULT_MAX_RETRIES, timeout: int = DEFAULT_API_TIMEOUT_SECONDS) -> Any:
            # It does NOT accept model or max_tokens as arguments. It uses config.ANTHROPIC_MODEL and hardcoded 4096.
            # So I should remove model and max_tokens arguments.
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
