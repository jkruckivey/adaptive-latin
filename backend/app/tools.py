"""
Resource Loading and Learner Model Management

This module provides functions for loading resources from the resource bank
and managing learner models (progress tracking).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import config
from .spaced_repetition import (
    initialize_review_data,
    update_review_schedule,
    get_due_reviews,
    get_review_stats
)
import random

from .confidence import calculate_calibration, calculate_overall_calibration

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


# ============================================================================
# Resource Loading Functions
# ============================================================================

def load_resource(concept_id: str, resource_type: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a resource from the resource bank.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        resource_type: Type of resource ("text-explainer" or "examples")
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        Resource data as dictionary

    Raises:
        FileNotFoundError: If resource doesn't exist
        ValueError: If resource type is invalid
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)

        if resource_type == "text-explainer":
            resource_path = concept_dir / "resources" / "text-explainer.md"
            if not resource_path.exists():
                raise FileNotFoundError(f"Text explainer not found for {concept_id}")

            with open(resource_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Loaded text-explainer for {concept_id}")
            return {
                "type": "text",
                "concept_id": concept_id,
                "content": content
            }

        elif resource_type == "examples":
            resource_path = concept_dir / "resources" / "examples.json"
            if not resource_path.exists():
                raise FileNotFoundError(f"Examples not found for {concept_id}")

            with open(resource_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Loaded examples for {concept_id}")
            return {
                "type": "examples",
                "concept_id": concept_id,
                "examples": data.get("examples", [])
            }

        else:
            raise ValueError(f"Invalid resource_type: {resource_type}. Must be 'text-explainer' or 'examples'")

    except Exception as e:
        logger.error(f"Error loading resource {resource_type} for {concept_id}: {e}")
        raise


def load_assessment(concept_id: str, assessment_type: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load an assessment from the resource bank.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        assessment_type: Type of assessment ("dialogue", "written", or "applied")
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        Assessment data as dictionary

    Raises:
        FileNotFoundError: If assessment doesn't exist
        ValueError: If assessment type is invalid
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)

        if assessment_type not in ["dialogue", "written", "applied"]:
            raise ValueError(f"Invalid assessment_type: {assessment_type}. Must be 'dialogue', 'written', or 'applied'")

        assessment_file = f"{assessment_type}-prompts.json" if assessment_type in ["dialogue", "written"] else "applied-tasks.json"
        assessment_path = concept_dir / "assessments" / assessment_file

        if not assessment_path.exists():
            raise FileNotFoundError(f"Assessment {assessment_type} not found for {concept_id}")

        with open(assessment_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {assessment_type} assessment for {concept_id}")
        return data

    except Exception as e:
        logger.error(f"Error loading assessment {assessment_type} for {concept_id}: {e}")
        raise


def load_concept_metadata(concept_id: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load metadata for a concept.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        Metadata dictionary

    Raises:
        FileNotFoundError: If metadata doesn't exist
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)
        metadata_path = concept_dir / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for {concept_id}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        logger.info(f"Loaded metadata for {concept_id}")
        return metadata

    except Exception as e:
        logger.error(f"Error loading metadata for {concept_id}: {e}")
        raise


# ============================================================================
# Learner Model Management Functions
# ============================================================================

def create_learner_model(
    learner_id: str,
    learner_name: Optional[str] = None,
    profile: Optional[Dict[str, Any]] = None,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new learner model with initial state.

    Args:
        learner_id: Unique identifier for the learner
        learner_name: Learner's name (optional)
        profile: Learner profile from onboarding (optional)
        course_id: Course to enroll in (optional, defaults to DEFAULT_COURSE_ID)

    Returns:
        New learner model dictionary

    Raises:
        ValueError: If learner already exists
    """
    try:
        learner_file = config.get_learner_file(learner_id)

        if learner_file.exists():
            raise ValueError(f"Learner {learner_id} already exists")

        # Initialize learner model
        from .constants import PRACTICE_MODE_DEFAULT

        learner_model = {
            "learner_id": learner_id,
            "learner_name": learner_name,
            "profile": profile or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_course": course_id or config.DEFAULT_COURSE_ID,  # Support for multiple courses
            "current_concept": "concept-001",
            "concepts": {},
            "question_history": [],  # Track recent questions to avoid repetition
            "practice_mode": PRACTICE_MODE_DEFAULT,  # Choice & agency: learners can toggle practice mode
            "overall_progress": {
                "concepts_completed": 0,
                "concepts_in_progress": 1,
                "total_assessments": 0,
                "average_calibration_accuracy": 0.0
            }
        }

        # Save to disk
        save_learner_model(learner_id, learner_model)

        logger.info(f"Created new learner model for {learner_id} with course {learner_model['current_course']}")
        return learner_model

    except Exception as e:
        logger.error(f"Error creating learner model for {learner_id}: {e}")
        raise


def load_learner_model(learner_id: str) -> Dict[str, Any]:
    """
    Load an existing learner model.

    Args:
        learner_id: Unique identifier for the learner

    Returns:
        Learner model dictionary

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        learner_file = config.get_learner_file(learner_id)

        if not learner_file.exists():
            raise FileNotFoundError(f"Learner {learner_id} not found")

        with open(learner_file, "r", encoding="utf-8") as f:
            learner_model = json.load(f)

        logger.info(f"Loaded learner model for {learner_id}")
        return learner_model

    except Exception as e:
        logger.error(f"Error loading learner model for {learner_id}: {e}")
        raise


def save_learner_model(learner_id: str, model: Dict[str, Any]) -> None:
    """
    Save a learner model to disk.

    Args:
        learner_id: Unique identifier for the learner
        model: Learner model dictionary to save

    Raises:
        IOError: If save fails
    """
    try:
        learner_file = config.get_learner_file(learner_id)

        # Ensure directory exists
        config.ensure_directories()

        # Update timestamp
        model["updated_at"] = datetime.now().isoformat()

        # Save to disk
        with open(learner_file, "w", encoding="utf-8") as f:
            json.dump(model, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved learner model for {learner_id}")

    except Exception as e:
        logger.error(f"Error saving learner model for {learner_id}: {e}")
        raise


def update_learner_model(
    learner_id: str,
    concept_id: str,
    assessment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update learner model with new assessment data.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Concept being assessed
        assessment_data: Assessment results including score, confidence, calibration

    Returns:
        Updated learner model

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        # Load existing model
        logger.info(f"🔍 update_learner_model called for learner={learner_id}, concept={concept_id}")
        logger.info(f"📊 Assessment data: type={assessment_data.get('type')}, score={assessment_data.get('score')}, confidence={assessment_data.get('self_confidence')}")

        model = load_learner_model(learner_id)

        # Initialize concept tracking if not exists
        if concept_id not in model["concepts"]:
            logger.info(f"🆕 Initializing new concept entry for {concept_id}")
            model["concepts"][concept_id] = {
                "concept_id": concept_id,
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "assessments": [],
                "confidence_history": [],
                "mastery_score": 0.0,
                "review_data": initialize_review_data(concept_id)
            }
        else:
            logger.info(f"📝 Updating existing concept entry for {concept_id}")

        concept_data = model["concepts"][concept_id]

        # Add assessment record
        assessment_record = {
            "timestamp": datetime.now().isoformat(),
            "type": assessment_data.get("type", "dialogue"),
            "score": assessment_data.get("score", 0.0),
            "self_confidence": assessment_data.get("self_confidence"),
            "calibration": assessment_data.get("calibration"),
            "prompt_id": assessment_data.get("prompt_id")
        }
        concept_data["assessments"].append(assessment_record)
        logger.info(f"✅ Added assessment record. Total assessments for {concept_id}: {len(concept_data['assessments'])}")

        # Add confidence tracking if present
        if "calibration" in assessment_data:
            confidence_record = {
                "timestamp": datetime.now().isoformat(),
                "self_confidence": assessment_data.get("self_confidence"),
                "actual_score": assessment_data.get("score"),
                "expected_confidence": assessment_data["calibration"].get("expected_confidence"),
                "error": assessment_data["calibration"].get("calibration_error"),
                "calibration": assessment_data["calibration"].get("calibration")
            }
            concept_data["confidence_history"].append(confidence_record)

        # Update mastery score (average of all assessments)
        if concept_data["assessments"]:
            scores = [a["score"] for a in concept_data["assessments"]]
            concept_data["mastery_score"] = sum(scores) / len(scores)

        # Update spaced repetition schedule
        if "review_data" not in concept_data:
            concept_data["review_data"] = initialize_review_data(concept_id)

        # Get calibration error for review schedule calculation
        calibration_error = 0
        if "calibration" in assessment_data:
            calibration_error = assessment_data["calibration"].get("calibration_error", 0)

        concept_data["review_data"] = update_review_schedule(
            review_data=concept_data["review_data"],
            score=assessment_data.get("score", 0.0),
            confidence_error=calibration_error
        )

        # Update overall progress
        model["overall_progress"]["total_assessments"] = sum(
            len(c["assessments"]) for c in model["concepts"].values()
        )
        logger.info(f"📈 Updated total_assessments count: {model['overall_progress']['total_assessments']}")

        # Save updated model
        save_learner_model(learner_id, model)

        logger.info(f"💾 Saved learner model for {learner_id}, concept {concept_id}")
        logger.info(f"✨ Summary: {len(model['concepts'])} concepts tracked, {model['overall_progress']['total_assessments']} total assessments")
        return model

    except Exception as e:
        logger.error(f"Error updating learner model for {learner_id}: {e}")
        raise


def record_assessment_and_check_completion(
    learner_id: str,
    concept_id: str,
    is_correct: bool,
    confidence: Optional[int],
    question_type: str,
    practice_mode: bool = False,
) -> Dict[str, Any]:
    """Record an assessment attempt and determine mastery completion.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Concept currently being practiced
        is_correct: Whether the learner's answer was correct
        confidence: Self-reported confidence rating (1-5) or None
        question_type: Type of question answered (multiple-choice, fill-blank, dialogue)
        practice_mode: Whether this is practice mode (doesn't count toward mastery)

    Returns:
        Dictionary with mastery tracking details including updated mastery score,
        assessment count, completion flag, and total concepts completed.
        In practice mode, returns simplified response without updating mastery.
    """

    try:
        logger.info(f"🎯 record_assessment_and_check_completion called: learner={learner_id}, concept={concept_id}, correct={is_correct}, confidence={confidence}, type={question_type}, practice={practice_mode}")

        # Translate correctness into a mastery score contribution
        score = 1.0 if is_correct else 0.0

        # In practice mode, don't record or update mastery
        if practice_mode:
            logger.info(f"⏸️ Practice mode: Not recording assessment for {learner_id}, {concept_id}")
            return {
                "concept_completed": False,
                "concepts_completed_total": 0,
                "mastery_score": 0.0,
                "assessments_count": 0,
                "next_concept": None,
                "calibration": None,
                "practice_mode": True  # Flag to frontend that this was practice
            }

        # Build assessment payload for the learner model helper
        assessment_data: Dict[str, Any] = {
            "type": question_type or "assessment",
            "score": score,
            "self_confidence": confidence,
        }
        logger.info(f"📦 Built assessment_data: {assessment_data}")

        calibration_data = None
        if confidence is not None:
            calibration_data = calculate_calibration(int(confidence), score)
            assessment_data["calibration"] = calibration_data

        learner_model = update_learner_model(
            learner_id=learner_id,
            concept_id=concept_id,
            assessment_data=assessment_data,
        )

        concept_data = learner_model["concepts"][concept_id]
        mastery_info = calculate_mastery(learner_id, concept_id)
        mastery_score = mastery_info.get("mastery_score", concept_data.get("mastery_score", 0.0))
        assessments_count = len(concept_data.get("assessments", []))

        concept_completed = mastery_info.get("mastery_achieved", False)
        next_concept = None

        if concept_completed:
            # Mark concept as completed and advance to the next one when available
            if concept_data.get("status") != "completed":
                concept_data["status"] = "completed"
                concept_data["completed_at"] = datetime.now().isoformat()

            next_concept = get_next_concept(concept_id)
            if next_concept:
                learner_model["current_concept"] = next_concept

                if next_concept not in learner_model["concepts"]:
                    learner_model["concepts"][next_concept] = {
                        "concept_id": next_concept,
                        "status": "in_progress",
                        "started_at": datetime.now().isoformat(),
                        "assessments": [],
                        "confidence_history": [],
                        "mastery_score": 0.0,
                        "review_data": initialize_review_data(next_concept),
                    }

        # Update overall progress counters
        concepts_completed_total = sum(
            1 for data in learner_model["concepts"].values() if data.get("status") == "completed"
        )
        concepts_in_progress = sum(
            1 for data in learner_model["concepts"].values() if data.get("status") == "in_progress"
        )

        learner_model["overall_progress"]["concepts_completed"] = concepts_completed_total
        learner_model["overall_progress"]["concepts_in_progress"] = concepts_in_progress

        # Refresh calibration accuracy when new confidence data is provided
        if confidence is not None:
            all_confidence = []
            for data in learner_model["concepts"].values():
                all_confidence.extend(data.get("confidence_history", []))

            if all_confidence:
                overall_calibration = calculate_overall_calibration(all_confidence)
                learner_model["overall_progress"]["average_calibration_accuracy"] = overall_calibration.get(
                    "overall_accuracy", 0.0
                )

        # Persist any progress/status updates performed above
        save_learner_model(learner_id, learner_model)

        return {
            "concept_completed": concept_completed,
            "concepts_completed_total": concepts_completed_total,
            "mastery_score": mastery_score,
            "assessments_count": assessments_count,
            "next_concept": next_concept,
            "calibration": calibration_data,
        }

    except Exception as e:
        logger.error(
            f"Error recording assessment for {learner_id}, {concept_id}: {e}"
        )
        raise


def calculate_mastery(learner_id: str, concept_id: str) -> Dict[str, Any]:
    """
    Calculate mastery level for a concept.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Concept to check mastery for

    Returns:
        Dictionary with mastery analysis

    Raises:
        FileNotFoundError: If learner doesn't exist
        ValueError: If concept not started
    """
    try:
        model = load_learner_model(learner_id)

        if concept_id not in model["concepts"]:
            raise ValueError(f"Concept {concept_id} not started for learner {learner_id}")

        concept_data = model["concepts"][concept_id]
        assessments = concept_data["assessments"]

        if not assessments:
            return {
                "concept_id": concept_id,
                "mastery_achieved": False,
                "mastery_score": 0.0,
                "assessments_completed": 0,
                "recommendation": "continue",
                "reason": "No assessments completed yet"
            }

        # Calculate metrics with spaced repetition forgiveness
        from .constants import LEARNING_PHASE_QUESTIONS, LEARNING_PHASE_WEIGHT, MASTERY_PHASE_WEIGHT

        scores = [a["score"] for a in assessments]
        num_assessments = len(assessments)

        # Apply forgiveness weighting: early questions (learning phase) weighted less
        # This prevents early mistakes from permanently hurting mastery score
        weighted_scores = []
        total_weight = 0

        for i, score in enumerate(scores):
            # First N questions are "learning phase" with reduced weight
            if i < LEARNING_PHASE_QUESTIONS:
                weight = LEARNING_PHASE_WEIGHT  # 50% weight
            else:
                weight = MASTERY_PHASE_WEIGHT   # 100% weight

            weighted_scores.append(score * weight)
            total_weight += weight

        # Calculate weighted average
        weighted_avg = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0

        # Use sliding window for recent performance (with weighting applied)
        window_size = config.MASTERY_WINDOW_SIZE
        recent_scores = scores[-window_size:] if len(scores) > window_size else scores

        # Also calculate recent weighted average for display
        recent_weighted = []
        recent_weight = 0
        for i, score in enumerate(scores[-window_size:]):
            actual_index = len(scores) - window_size + i if len(scores) > window_size else i
            if actual_index < LEARNING_PHASE_QUESTIONS:
                weight = LEARNING_PHASE_WEIGHT
            else:
                weight = MASTERY_PHASE_WEIGHT
            recent_weighted.append(score * weight)
            recent_weight += weight

        avg_score = sum(recent_weighted) / recent_weight if recent_weight > 0 else 0.0

        logger.info(f"Mastery calculation for {concept_id}: {len(recent_scores)} recent assessments, weighted_avg={avg_score:.2f}, overall_weighted={weighted_avg:.2f}")

        # Check mastery criteria
        mastery_achieved = (
            avg_score >= config.MASTERY_THRESHOLD and
            num_assessments >= config.MIN_ASSESSMENTS_FOR_MASTERY
        )

        # Determine recommendation
        if mastery_achieved:
            recommendation = "progress"
            reason = f"Mastery achieved: {avg_score:.2f} average over last {len(recent_scores)} assessments"
        elif avg_score >= config.CONTINUE_THRESHOLD:
            recommendation = "continue"
            reason = f"Good progress ({avg_score:.2f}), continue practicing"
        else:
            recommendation = "support"
            reason = f"Needs support ({avg_score:.2f}), consider different approach or review prerequisites"

        result = {
            "concept_id": concept_id,
            "mastery_achieved": mastery_achieved,
            "mastery_score": avg_score,
            "assessments_completed": num_assessments,
            "recommendation": recommendation,
            "reason": reason,
            "recent_scores": scores[-3:] if len(scores) >= 3 else scores
        }

        logger.info(f"Calculated mastery for {learner_id}, {concept_id}: {avg_score:.2f}")
        return result

    except Exception as e:
        logger.error(f"Error calculating mastery for {learner_id}, {concept_id}: {e}")
        raise


def validate_concept_completeness(concept_id: str, course_id: Optional[str] = None) -> bool:
    """
    Validate that a concept has minimum viable resources for learning.

    Checks that required files exist and contain content (not empty scaffolds).
    Based on peer review feedback to prevent crashes from empty concept directories.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        True if concept has all required resources, False otherwise
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)

        # Check that concept directory exists
        if not concept_dir.exists():
            logger.warning(f"Concept directory does not exist: {concept_id}")
            return False

        # Define required files with minimum size requirements
        required_files = [
            (concept_dir / "metadata.json", 50),  # At least 50 bytes (not empty JSON)
            (concept_dir / "resources" / "text-explainer.md", 100),  # At least 100 bytes
            (concept_dir / "assessments" / "dialogue-prompts.json", 100),  # At least 100 bytes
        ]

        # Validate each required file
        for file_path, min_size in required_files:
            if not file_path.exists():
                logger.warning(f"Required file missing for {concept_id}: {file_path.name}")
                return False

            # Check file has content (not empty scaffold)
            if file_path.stat().st_size < min_size:
                logger.warning(f"Required file too small for {concept_id}: {file_path.name} ({file_path.stat().st_size} bytes < {min_size} bytes)")
                return False

        logger.info(f"Concept {concept_id} validation passed - all required resources present")
        return True

    except Exception as e:
        logger.error(f"Error validating concept completeness for {concept_id}: {e}")
        return False


def get_next_concept(current_concept_id: str, course_id: Optional[str] = None) -> Optional[str]:
    """
    Determine the next concept in the learning path.

    Args:
        current_concept_id: Current concept ID (e.g., "concept-001")
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        Next concept ID or None if at the end
    """
    # Extract number from concept-XXX
    try:
        current_num = int(current_concept_id.split("-")[1])
        next_num = current_num + 1

        # Check if next concept exists (we have 7 concepts)
        if next_num <= 7:
            next_concept_id = f"concept-{next_num:03d}"

            # Verify it exists in resource bank AND has complete content
            # (Based on peer review: prevent crashes from empty concept directories)
            next_concept_dir = config.get_concept_dir(next_concept_id, course_id)
            if next_concept_dir.exists() and validate_concept_completeness(next_concept_id, course_id):
                logger.info(f"Next concept after {current_concept_id} is {next_concept_id}")
                return next_concept_id
            else:
                logger.warning(f"Concept {next_concept_id} exists but is incomplete - no content to progress to")
                return None

        logger.info(f"No next concept after {current_concept_id} - reached end of learning path")
        return None

    except Exception as e:
        logger.error(f"Error determining next concept after {current_concept_id}: {e}")
        return None


def list_all_concepts(course_id: str = None) -> List[str]:
    """
    Get a list of all available concepts for a course.

    Supports both module-based and flat structures:
    - Module-based: checks inside module-xxx directories
    - Flat: checks directly in course directory

    Args:
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        List of concept IDs (sorted)
    """
    try:
        if course_id is None:
            course_id = config.DEFAULT_COURSE_ID

        concepts = []
        course_dir = config.get_course_dir(course_id)

        if course_dir.exists():
            # First check for module-based structure
            has_modules = False
            for item in course_dir.iterdir():
                if item.is_dir() and item.name.startswith("module-"):
                    has_modules = True
                    # Look for concepts inside this module
                    for concept_dir in item.iterdir():
                        if concept_dir.is_dir() and concept_dir.name.startswith("concept-"):
                            concepts.append(concept_dir.name)

            # If no modules found, check for flat structure
            if not has_modules:
                for concept_dir in course_dir.iterdir():
                    if concept_dir.is_dir() and concept_dir.name.startswith("concept-"):
                        concepts.append(concept_dir.name)

        concepts.sort()
        logger.info(f"Found {len(concepts)} concepts in {course_id}")
        return concepts

    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        return []


def list_all_modules(course_id: str = None) -> List[Dict[str, Any]]:
    """
    Get a list of all modules in a course with their concepts.

    Args:
        course_id: Course identifier (defaults to DEFAULT_COURSE_ID)

    Returns:
        List of module dictionaries with structure:
        [
            {
                "id": "module-001",
                "title": "Module Title",
                "module_learning_outcomes": [...],
                "concepts": ["concept-001", "concept-002"]
            },
            ...
        ]
    """
    try:
        if course_id is None:
            course_id = config.DEFAULT_COURSE_ID

        modules = []
        course_dir = config.get_course_dir(course_id)

        if course_dir.exists():
            module_dirs = sorted([d for d in course_dir.iterdir() if d.is_dir() and d.name.startswith("module-")])

            for module_dir in module_dirs:
                module_id = module_dir.name

                # Load module metadata
                metadata_path = module_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            module_metadata = json.load(f)

                        # List concepts in this module
                        concepts = sorted([c.name for c in module_dir.iterdir() if c.is_dir() and c.name.startswith("concept-")])

                        modules.append({
                            "id": module_id,
                            "title": module_metadata.get("title", module_id),
                            "module_learning_outcomes": module_metadata.get("module_learning_outcomes", []),
                            "concepts": concepts
                        })
                    except Exception as e:
                        logger.warning(f"Could not load metadata for module {module_id}: {e}")

        logger.info(f"Found {len(modules)} modules in {course_id}")
        return modules

    except Exception as e:
        logger.error(f"Error listing modules: {e}")
        return []


def list_all_courses() -> List[Dict[str, Any]]:
    """
    Get a list of all available courses from both built-in and user-created courses.

    Returns:
        List of course metadata dictionaries with structure:
        [
            {
                "course_id": "latin-grammar",
                "title": "Latin Grammar Fundamentals",
                "domain": "language",
                "description": "...",
                ...
            },
            ...
        ]
    """
    try:
        courses = []

        # Scan built-in courses in RESOURCE_BANK_DIR
        if config.RESOURCE_BANK_DIR.exists():
            for item in config.RESOURCE_BANK_DIR.iterdir():
                if item.is_dir() and item.name != "user-courses":
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        try:
                            course_metadata = load_course_metadata(item.name)
                            if course_metadata:
                                courses.append(course_metadata)
                        except Exception as e:
                            logger.warning(f"Could not load metadata for course {item.name}: {e}")

        # Scan user-created courses in USER_COURSES_DIR
        if config.USER_COURSES_DIR.exists():
            for item in config.USER_COURSES_DIR.iterdir():
                if item.is_dir():
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        try:
                            course_metadata = load_course_metadata(item.name)
                            if course_metadata:
                                courses.append(course_metadata)
                        except Exception as e:
                            logger.warning(f"Could not load metadata for course {item.name}: {e}")

        logger.info(f"Found {len(courses)} total courses")
        return courses

    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        return []


def load_course_metadata(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata for a specific course.

    Args:
        course_id: Course identifier

    Returns:
        Course metadata dictionary, or None if not found

    Raises:
        FileNotFoundError: If course metadata doesn't exist
    """
    try:
        course_dir = config.get_course_dir(course_id)
        metadata_file = course_dir / "metadata.json"

        if not metadata_file.exists():
            logger.warning(f"Course metadata not found: {metadata_file}")
            return None

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Ensure course_id is set
        if "course_id" not in metadata:
            metadata["course_id"] = course_id

        logger.info(f"Loaded metadata for course: {course_id}")
        logger.info(f"Metadata keys: {list(metadata.keys())}")
        logger.info(f"onboarding_questions present: {'onboarding_questions' in metadata}")
        if "onboarding_questions" in metadata:
            logger.info(f"onboarding_questions count: {len(metadata['onboarding_questions'])}")
        return metadata

    except Exception as e:
        logger.error(f"Error loading course metadata for {course_id}: {e}")
        return None


def delete_course(course_id: str) -> bool:
    """
    Delete a course and all its content.

    Args:
        course_id: Course identifier

    Returns:
        True if successful, False if course not found
    """
    try:
        import shutil
        course_dir = config.get_course_dir(course_id)

        if not course_dir.exists():
            logger.warning(f"Course not found for deletion: {course_id}")
            return False

        shutil.rmtree(course_dir)
        logger.info(f"Deleted course: {course_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {e}")
        return False


def import_course_data(export_data: Dict[str, Any], new_course_id: Optional[str] = None, overwrite: bool = False) -> str:
    """
    Import a course from exported JSON data.

    Args:
        export_data: Course data dictionary
        new_course_id: Optional new course ID (uses original if not provided)
        overwrite: Whether to overwrite existing course

    Returns:
        The course_id of the imported course

    Raises:
        ValueError: If course exists and overwrite is False
    """
    try:
        from datetime import datetime

        course_id = new_course_id or export_data.get("course_id")
        if not course_id:
            raise ValueError("Course ID must be provided")

        course_dir = config.get_course_dir(course_id)

        # Check if exists
        if course_dir.exists() and not overwrite:
            raise ValueError(f"Course '{course_id}' already exists. Use overwrite=True to replace.")

        # Create course directory
        course_dir.mkdir(parents=True, exist_ok=True)

        # Update timestamps
        now = datetime.now().isoformat()
        export_data["imported_at"] = now
        export_data["updated_at"] = now

        # Save metadata
        metadata_file = course_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Imported course: {course_id}")
        return course_id

    except Exception as e:
        logger.error(f"Error importing course: {e}")
        raise


def add_course_source(course_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a source to a course.

    Args:
        course_id: Course identifier
        source_data: Source information

    Returns:
        The created source with generated ID

    Raises:
        FileNotFoundError: If course doesn't exist
    """
    try:
        import uuid
        course_dir = config.get_course_dir(course_id)

        if not course_dir.exists():
            raise FileNotFoundError(f"Course not found: {course_id}")

        # Generate source ID if not provided
        source_id = source_data.get("id") or str(uuid.uuid4())
        source_data["id"] = source_id

        # Load or create sources file
        sources_file = course_dir / "sources.json"
        if sources_file.exists():
            with open(sources_file, "r", encoding="utf-8") as f:
                sources = json.load(f)
        else:
            sources = []

        # Add new source
        sources.append(source_data)

        # Save
        with open(sources_file, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2)

        logger.info(f"Added source {source_id} to course {course_id}")
        return source_data

    except Exception as e:
        logger.error(f"Error adding source to course: {e}")
        raise


def add_concept_source(course_id: str, concept_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a source to a concept.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        source_data: Source information

    Returns:
        The created source with generated ID

    Raises:
        FileNotFoundError: If course or concept doesn't exist
    """
    try:
        import uuid
        concept_dir = config.get_concept_dir(concept_id, course_id)

        if not concept_dir.exists():
            raise FileNotFoundError(f"Concept not found: {concept_id} in course {course_id}")

        # Generate source ID if not provided
        source_id = source_data.get("id") or str(uuid.uuid4())
        source_data["id"] = source_id

        # Load or create sources file
        sources_file = concept_dir / "sources.json"
        if sources_file.exists():
            with open(sources_file, "r", encoding="utf-8") as f:
                sources = json.load(f)
        else:
            sources = []

        # Add new source
        sources.append(source_data)

        # Save
        with open(sources_file, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2)

        logger.info(f"Added source {source_id} to concept {concept_id}")
        return source_data

    except Exception as e:
        logger.error(f"Error adding source to concept: {e}")
        raise


def delete_source_from_course(course_id: str, source_id: str) -> bool:
    """
    Delete a source from a course.

    Args:
        course_id: Course identifier
        source_id: Source identifier

    Returns:
        True if successful, False if source not found
    """
    try:
        course_dir = config.get_course_dir(course_id)
        sources_file = course_dir / "sources.json"

        if not sources_file.exists():
            return False

        with open(sources_file, "r", encoding="utf-8") as f:
            sources = json.load(f)

        # Filter out the source
        new_sources = [s for s in sources if s.get("id") != source_id]

        if len(new_sources) == len(sources):
            return False  # Source not found

        # Save
        with open(sources_file, "w", encoding="utf-8") as f:
            json.dump(new_sources, f, indent=2)

        logger.info(f"Deleted source {source_id} from course {course_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting source from course: {e}")
        return False


def delete_source_from_concept(course_id: str, concept_id: str, source_id: str) -> bool:
    """
    Delete a source from a concept.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        source_id: Source identifier

    Returns:
        True if successful, False if source not found
    """
    try:
        concept_dir = config.get_concept_dir(concept_id, course_id)
        sources_file = concept_dir / "sources.json"

        if not sources_file.exists():
            return False

        with open(sources_file, "r", encoding="utf-8") as f:
            sources = json.load(f)

        # Filter out the source
        new_sources = [s for s in sources if s.get("id") != source_id]

        if len(new_sources) == len(sources):
            return False  # Source not found

        # Save
        with open(sources_file, "w", encoding="utf-8") as f:
            json.dump(new_sources, f, indent=2)

        logger.info(f"Deleted source {source_id} from concept {concept_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting source from concept: {e}")
        return False


def load_external_resources(concept_id: str = None, learner_profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Load curated external resources (videos, articles) for a concept.

    Args:
        concept_id: Concept identifier (e.g., "concept-001"), or None for general resources
        learner_profile: Learner profile to filter resources by learning preference

    Returns:
        List of external resource dictionaries

    Raises:
        FileNotFoundError: If external resources file doesn't exist
    """
    try:
        resources_file = config.RESOURCE_BANK_DIR.parent / "external-resources.json"

        if not resources_file.exists():
            logger.warning("External resources file not found")
            return []

        with open(resources_file, "r", encoding="utf-8") as f:
            all_resources = json.load(f)

        # Get resources for the concept
        concept_key = concept_id if concept_id else "general"
        if concept_key not in all_resources:
            logger.info(f"No external resources found for {concept_key}")
            return []

        resources = all_resources[concept_key]["resources"]

        # Filter by learner profile if provided
        if learner_profile:
            learning_preference = learner_profile.get("learningStyle", "")
            preference_mapping = {
                "narrative": ["narrative_learners", "stories", "contextual", "article"],
                "varied": ["visual_learners", "video", "practice", "interactive"],
                "dialogue": ["interactive", "conversational", "guided"]
            }

            # Prioritize resources matching learner's preference
            recommended_tags = preference_mapping.get(learning_preference, [])
            if recommended_tags:
                # Sort resources to put matching ones first
                resources = sorted(
                    resources,
                    key=lambda r: any(tag in r.get("recommended_for", []) for tag in recommended_tags),
                    reverse=True
                )

        logger.info(f"Loaded {len(resources)} external resources for {concept_key}")
        return resources

    except Exception as e:
        logger.error(f"Error loading external resources: {e}")
        return []


# ============================================================================
# Cumulative Review Functions
# ============================================================================

def get_eligible_concepts_for_cumulative(learner_id: str, min_mastery: float = 0.6) -> List[str]:
    """
    Get concepts eligible for cumulative review (those with sufficient mastery).

    Args:
        learner_id: Unique identifier for the learner
        min_mastery: Minimum mastery score to be eligible for cumulative review (default 0.6)

    Returns:
        List of concept IDs eligible for cumulative review

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        model = load_learner_model(learner_id)

        eligible_concepts = []
        for concept_id, concept_data in model["concepts"].items():
            mastery_score = concept_data.get("mastery_score", 0.0)
            if mastery_score >= min_mastery:
                eligible_concepts.append(concept_id)

        logger.info(f"Found {len(eligible_concepts)} eligible concepts for cumulative review (mastery >= {min_mastery})")
        return eligible_concepts

    except Exception as e:
        logger.error(f"Error getting eligible concepts for {learner_id}: {e}")
        raise


def select_concepts_for_cumulative(learner_id: str, count: int = 3) -> List[str]:
    """
    Select random concepts for cumulative review questions.

    Args:
        learner_id: Unique identifier for the learner
        count: Number of concepts to select (default 3, will select min of count or available)

    Returns:
        List of concept IDs for cumulative review

    Raises:
        FileNotFoundError: If learner doesn't exist
        ValueError: If no eligible concepts available
    """
    try:
        eligible = get_eligible_concepts_for_cumulative(learner_id)

        if not eligible:
            raise ValueError(f"No eligible concepts for cumulative review (none with mastery >= 0.6)")

        # Select min(count, available) concepts randomly
        num_to_select = min(count, len(eligible))
        selected = random.sample(eligible, num_to_select)

        logger.info(f"Selected {len(selected)} concepts for cumulative review: {selected}")
        return selected

    except Exception as e:
        logger.error(f"Error selecting concepts for cumulative review: {e}")
        raise


def should_show_cumulative_review(learner_id: str) -> bool:
    """
    Determine if cumulative review should be shown based on learner progress.

    Criteria:
    - Learner has completed at least 3 concepts with mastery >= 0.6
    - Last assessment was not a cumulative review
    - Random chance (30%) to encourage spaced interleaving

    Args:
        learner_id: Unique identifier for the learner

    Returns:
        True if cumulative review should be shown

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        model = load_learner_model(learner_id)

        # Check if at least 3 concepts are eligible
        eligible = get_eligible_concepts_for_cumulative(learner_id)
        if len(eligible) < 3:
            logger.info(f"Not enough eligible concepts for cumulative review: {len(eligible)}/3")
            return False

        # Check question history to avoid consecutive cumulative reviews
        question_history = model.get("question_history", [])
        if question_history:
            last_question = question_history[-1]
            if last_question.get("is_cumulative", False):
                logger.info("Last question was cumulative, skipping cumulative review")
                return False

        # 50% chance to show cumulative review (increased from 30% based on student journey audit)
        show_cumulative = random.random() < 0.5
        logger.info(f"Cumulative review decision: {show_cumulative} (50% chance)")
        return show_cumulative

    except Exception as e:
        logger.error(f"Error determining cumulative review for {learner_id}: {e}")
        return False


def should_show_confidence_rating(learner_id: str, current_concept_id: str) -> bool:
    """
    Determine if confidence rating should be shown based on learner performance.

    Adaptive frequency based on student journey audit feedback:
    - High performers (mastery >= 0.7): confidence every 3-5 questions
    - Struggling learners (mastery < 0.7): confidence every 1-2 questions
    - Random sampling to avoid predictability

    Args:
        learner_id: Unique identifier for the learner
        current_concept_id: Current concept being practiced

    Returns:
        True if confidence rating should be shown

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        model = load_learner_model(learner_id)

        # Get current concept data
        concept_data = model.get("concepts", {}).get(current_concept_id, {})

        # Calculate mastery score (average of all assessments)
        assessments = concept_data.get("assessments", [])
        if not assessments:
            # First question - always show confidence
            logger.info("First question - showing confidence rating")
            return True

        mastery_score = sum(a["score"] for a in assessments) / len(assessments)

        # Count questions since last confidence rating
        confidence_history = concept_data.get("confidence_history", [])
        questions_since_rating = len(assessments) - len(confidence_history)

        # Determine threshold based on performance
        if mastery_score >= 0.7:
            # High performer: every 3-5 questions (with randomness)
            threshold = random.randint(3, 5)
            logger.info(f"High performer (mastery={mastery_score:.2f}): threshold={threshold}")
        else:
            # Struggling learner: every 1-2 questions
            threshold = random.randint(1, 2)
            logger.info(f"Struggling learner (mastery={mastery_score:.2f}): threshold={threshold}")

        # Show confidence if threshold reached
        show_confidence = questions_since_rating >= threshold
        logger.info(f"Questions since rating: {questions_since_rating}, Threshold: {threshold}, Show: {show_confidence}")

        return show_confidence

    except Exception as e:
        logger.error(f"Error determining confidence rating for {learner_id}: {e}")
        # Default to showing confidence on error
        return True


# ============================================================================
# Adaptive Scaffolding & Difficulty Adjustment
# ============================================================================

def calculate_recent_performance(learner_id: str, concept_id: str, window_size: int = 5) -> float:
    """
    Calculate learner's performance over recent questions.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being practiced
        window_size: Number of recent questions to consider (default 5)

    Returns:
        Performance ratio (0.0 to 1.0) representing proportion of correct answers

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        from .constants import DIFFICULTY_ASSESSMENT_WINDOW

        model = load_learner_model(learner_id)
        concept_data = model.get("concepts", {}).get(concept_id, {})
        assessments = concept_data.get("assessments", [])

        if not assessments:
            # No history yet, return neutral performance
            return 0.5

        # Use provided window size or constant
        window = window_size if window_size else DIFFICULTY_ASSESSMENT_WINDOW
        recent_assessments = assessments[-window:]

        # Calculate correctness ratio
        correct_count = sum(1 for a in recent_assessments if a.get("score", 0) >= 1.0)
        performance = correct_count / len(recent_assessments)

        logger.info(f"Recent performance for {concept_id}: {correct_count}/{len(recent_assessments)} = {performance:.2f}")
        return performance

    except Exception as e:
        logger.error(f"Error calculating recent performance for {learner_id}: {e}")
        return 0.5  # Return neutral on error


def select_question_difficulty(learner_id: str, concept_id: str) -> str:
    """
    Determine appropriate question difficulty based on recent performance.

    Implements adaptive scaffolding:
    - Below 40% recent performance -> easier questions (back to fundamentals)
    - 40-85% performance -> appropriate level (maintain challenge)
    - Above 85% performance -> harder questions (increase difficulty)

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being practiced

    Returns:
        Difficulty level string: "easier", "appropriate", or "harder"

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        from .constants import (
            DIFFICULTY_DOWN_THRESHOLD,
            DIFFICULTY_UP_THRESHOLD,
            DIFFICULTY_EASIER,
            DIFFICULTY_APPROPRIATE,
            DIFFICULTY_HARDER
        )

        recent_performance = calculate_recent_performance(learner_id, concept_id)

        if recent_performance < DIFFICULTY_DOWN_THRESHOLD:
            difficulty = DIFFICULTY_EASIER
            logger.info(f"Performance {recent_performance:.2f} < {DIFFICULTY_DOWN_THRESHOLD} -> {difficulty}")
        elif recent_performance > DIFFICULTY_UP_THRESHOLD:
            difficulty = DIFFICULTY_HARDER
            logger.info(f"Performance {recent_performance:.2f} > {DIFFICULTY_UP_THRESHOLD} -> {difficulty}")
        else:
            difficulty = DIFFICULTY_APPROPRIATE
            logger.info(f"Performance {recent_performance:.2f} in normal range -> {difficulty}")

        return difficulty

    except Exception as e:
        logger.error(f"Error selecting difficulty for {learner_id}: {e}")
        return "appropriate"  # Default to appropriate on error


def get_adaptive_mastery_threshold(learner_id: str, concept_id: str) -> float:
    """
    Get adaptive mastery threshold based on recent performance.

    Implements growth mindset by adjusting expectations:
    - Struggling learners (< 40%): lower threshold to 0.70 for achievable wins
    - Normal performance (40-85%): standard threshold 0.75
    - Excelling learners (> 85%): higher threshold 0.85 for challenge

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being practiced

    Returns:
        Mastery threshold (0.0 to 1.0)

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        from .constants import (
            DIFFICULTY_DOWN_THRESHOLD,
            DIFFICULTY_UP_THRESHOLD,
            MASTERY_THRESHOLD_STRUGGLING,
            MASTERY_THRESHOLD_NORMAL,
            MASTERY_THRESHOLD_EXCELLING
        )

        recent_performance = calculate_recent_performance(learner_id, concept_id)

        if recent_performance < DIFFICULTY_DOWN_THRESHOLD:
            threshold = MASTERY_THRESHOLD_STRUGGLING
            logger.info(f"Struggling (performance={recent_performance:.2f}) -> threshold={threshold}")
        elif recent_performance > DIFFICULTY_UP_THRESHOLD:
            threshold = MASTERY_THRESHOLD_EXCELLING
            logger.info(f"Excelling (performance={recent_performance:.2f}) -> threshold={threshold}")
        else:
            threshold = MASTERY_THRESHOLD_NORMAL
            logger.info(f"Normal performance ({recent_performance:.2f}) -> threshold={threshold}")

        return threshold

    except Exception as e:
        logger.error(f"Error getting adaptive mastery threshold for {learner_id}: {e}")
        return 0.75  # Default to normal threshold on error


def detect_struggle(learner_id: str, concept_id: str) -> Optional[Dict[str, Any]]:
    """
    Detect if learner is struggling and provide encouragement.

    Returns encouragement message if learner has answered incorrectly
    multiple times in a row or is below performance thresholds.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being practiced

    Returns:
        Dictionary with struggle detection info and encouragement message, or None

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        from .constants import (
            STRUGGLE_THRESHOLD_MILD,
            STRUGGLE_THRESHOLD_MODERATE,
            ENCOURAGEMENT_AFTER_N_INCORRECT,
            STRUGGLE_DETECTION_WINDOW
        )

        model = load_learner_model(learner_id)
        concept_data = model.get("concepts", {}).get(concept_id, {})
        assessments = concept_data.get("assessments", [])

        if len(assessments) < 2:
            # Not enough data to detect struggle
            return None

        # Check recent consecutive incorrect answers
        recent_assessments = assessments[-STRUGGLE_DETECTION_WINDOW:]
        consecutive_incorrect = 0
        for a in reversed(recent_assessments):
            if a.get("score", 0) < 1.0:
                consecutive_incorrect += 1
            else:
                break

        # Calculate recent performance
        recent_performance = calculate_recent_performance(learner_id, concept_id, STRUGGLE_DETECTION_WINDOW)

        # Determine struggle level and message
        if consecutive_incorrect >= ENCOURAGEMENT_AFTER_N_INCORRECT:
            struggle_level = "consecutive_incorrect"
            message = (
                "💪 Learning is a journey! These mistakes are valuable feedback. "
                "Each wrong answer helps you understand better. Keep going!"
            )
        elif recent_performance < STRUGGLE_THRESHOLD_MODERATE:
            struggle_level = "moderate"
            message = (
                "🌟 This is challenging, but you're making progress! "
                "Consider trying the preview mode or practice mode to explore without pressure. "
                "Remember: struggle means your brain is growing!"
            )
        elif recent_performance < STRUGGLE_THRESHOLD_MILD:
            struggle_level = "mild"
            message = (
                "👍 You're working through some tricky material. That's exactly how learning happens! "
                "Take your time, and remember you can always review the preview."
            )
        else:
            # No struggle detected
            return None

        logger.info(f"Struggle detected for {learner_id} on {concept_id}: level={struggle_level}, performance={recent_performance:.2f}")

        return {
            "struggle_level": struggle_level,
            "recent_performance": recent_performance,
            "consecutive_incorrect": consecutive_incorrect,
            "encouragement_message": message
        }

    except Exception as e:
        logger.error(f"Error detecting struggle for {learner_id}: {e}")
        return None


# ============================================================================
# Celebration Milestones
# ============================================================================

def detect_celebration_milestones(
    learner_id: str,
    concept_id: str,
    is_correct: bool,
    concept_completed: bool = False,
    concepts_completed_total: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Detect celebration-worthy milestones and generate motivational messages.

    Celebrates:
    - Streaks (3, 5, 10 correct in a row)
    - Concept completion (first, halfway, final)
    - Comeback victories (recovered from struggle)
    - Mastery achievement

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being practiced
        is_correct: Whether the current answer was correct
        concept_completed: Whether this question completed the concept
        concepts_completed_total: Total concepts completed so far

    Returns:
        Dictionary with celebration info and message, or None

    Raises:
        FileNotFoundError: If learner doesn't exist
    """
    try:
        from .constants import (
            CELEBRATION_STREAK_SHORT,
            CELEBRATION_STREAK_MEDIUM,
            CELEBRATION_STREAK_LONG,
            CELEBRATE_FIRST_CONCEPT,
            CELEBRATE_HALFWAY_POINT,
            CELEBRATE_FINAL_CONCEPT,
            CELEBRATION_COMEBACK
        )

        model = load_learner_model(learner_id)
        concept_data = model.get("concepts", {}).get(concept_id, {})
        assessments = concept_data.get("assessments", [])

        celebration_message = None
        celebration_type = None

        # Check for concept completion milestones
        if concept_completed:
            if concepts_completed_total == 1 and CELEBRATE_FIRST_CONCEPT:
                celebration_type = "first_concept"
                celebration_message = (
                    "🎉 Congratulations! You've completed your first concept! "
                    "This is a major milestone. Keep up the great work!"
                )
            elif concepts_completed_total == 4 and CELEBRATE_HALFWAY_POINT:  # Halfway through 7 concepts
                celebration_type = "halfway"
                celebration_message = (
                    "⭐ Halfway there! You've completed 4 out of 7 concepts. "
                    "You're making excellent progress on your Latin journey!"
                )
            elif concepts_completed_total == 7 and CELEBRATE_FINAL_CONCEPT:
                celebration_type = "course_complete"
                celebration_message = (
                    "🏆 AMAZING! You've completed ALL 7 concepts! "
                    "You've mastered the fundamentals of Latin grammar. Congratulations!"
                )
            elif concept_completed:
                celebration_type = "concept_complete"
                celebration_message = (
                    f"✅ Concept mastered! That's {concepts_completed_total} down. "
                    "Ready for the next challenge?"
                )

        # Check for streak milestones (only if currently correct)
        if is_correct and not celebration_message:
            # Count consecutive correct answers
            consecutive_correct = 0
            for assessment in reversed(assessments):
                if assessment.get("score", 0) >= 1.0:
                    consecutive_correct += 1
                else:
                    break

            if consecutive_correct >= CELEBRATION_STREAK_LONG:
                celebration_type = "long_streak"
                celebration_message = (
                    f"🔥 {consecutive_correct} in a row! You're unstoppable! "
                    "This kind of consistency shows real mastery."
                )
            elif consecutive_correct >= CELEBRATION_STREAK_MEDIUM:
                celebration_type = "medium_streak"
                celebration_message = (
                    f"⚡ {consecutive_correct} correct in a row! You're on fire! "
                    "Keep this momentum going!"
                )
            elif consecutive_correct >= CELEBRATION_STREAK_SHORT:
                celebration_type = "short_streak"
                celebration_message = (
                    f"✨ {consecutive_correct} in a row! Nice streak! "
                    "You're really getting the hang of this."
                )

        # Check for comeback victory (recovered from struggle)
        if is_correct and not celebration_message and CELEBRATION_COMEBACK and len(assessments) >= 6:
            # Look at last 10 questions
            recent_window = assessments[-10:] if len(assessments) >= 10 else assessments

            # Check if they struggled earlier but are doing well now
            first_half = recent_window[:len(recent_window)//2]
            second_half = recent_window[len(recent_window)//2:]

            first_half_score = sum(a.get("score", 0) for a in first_half) / len(first_half) if first_half else 0
            second_half_score = sum(a.get("score", 0) for a in second_half) / len(second_half) if second_half else 0

            # Comeback = was struggling (< 40%) but now excelling (> 70%)
            if first_half_score < 0.40 and second_half_score > 0.70:
                celebration_type = "comeback"
                celebration_message = (
                    "💪 Incredible comeback! You struggled at first but you didn't give up. "
                    "This shows real growth mindset - you're learning from mistakes!"
                )

        if celebration_message:
            logger.info(f"Celebration milestone for {learner_id}: {celebration_type}")
            return {
                "celebration_type": celebration_type,
                "celebration_message": celebration_message
            }

        return None

    except Exception as e:
        logger.error(f"Error detecting celebration for {learner_id}: {e}")
        return None


# ============================================================================
# Assessment Personalization Functions
# ============================================================================

def personalize_assessment_prompt(
    prompt_data: Dict[str, Any],
    learner_profile: Dict[str, Any]
) -> str:
    """
    Personalize an assessment prompt based on learner's interests and background.

    Uses scenario templates to adapt questions to learner's context while preserving
    the learning objective and assessment validity.

    Args:
        prompt_data: Assessment prompt dictionary containing:
            - base_prompt: Default question
            - scenario_templates: Interest-specific question variations
            - scenario_examples: Context data for templates
        learner_profile: Learner profile containing:
            - interests: String or list of learner interests
            - background: Background description

    Returns:
        Personalized prompt string

    Example:
        >>> prompt = {
        ...     "base_prompt": "How do you identify first declension?",
        ...     "scenario_templates": {
        ...         "history": "You're reading an inscription...",
        ...         "mythology": "In a myth about gods..."
        ...     }
        ... }
        >>> profile = {"interests": "Roman history, archaeology"}
        >>> personalize_assessment_prompt(prompt, profile)
        "You're reading an inscription..."
    """
    try:
        # Get base prompt as fallback
        base_prompt = prompt_data.get("base_prompt", "")

        # Check if personalization is enabled for this assessment
        scenario_templates = prompt_data.get("scenario_templates", {})
        if not scenario_templates:
            logger.debug("No scenario templates available, using base prompt")
            return base_prompt

        # Extract learner interests
        interests = learner_profile.get("interests", "")
        if isinstance(interests, list):
            interests = ", ".join(interests)
        interests = interests.lower()

        logger.debug(f"Learner interests: {interests}")
        logger.debug(f"Available scenarios: {list(scenario_templates.keys())}")

        # Match interests to scenario categories
        # Priority order: history, archaeology, mythology, literature, default
        if any(keyword in interests for keyword in ["history", "historical", "roman history", "ancient history", "inscriptions"]):
            selected_scenario = "history"
        elif any(keyword in interests for keyword in ["archaeology", "archaeological", "excavation", "artifacts", "sites"]):
            selected_scenario = "archaeology"
        elif any(keyword in interests for keyword in ["mythology", "mythological", "gods", "goddesses", "myths", "legends"]):
            selected_scenario = "mythology"
        elif any(keyword in interests for keyword in ["literature", "literary", "poetry", "poems", "reading", "books"]):
            selected_scenario = "literature"
        else:
            selected_scenario = "default"

        # Get the personalized prompt
        if selected_scenario in scenario_templates:
            personalized_prompt = scenario_templates[selected_scenario]
            logger.info(f"Personalized prompt using scenario: {selected_scenario}")
            return personalized_prompt
        elif "default" in scenario_templates:
            logger.info("Using default scenario template")
            return scenario_templates["default"]
        else:
            logger.info("No matching scenario, using base prompt")
            return base_prompt

    except Exception as e:
        logger.error(f"Error personalizing prompt: {e}")
        return prompt_data.get("base_prompt", "")


def select_personalized_dialogue_prompt(
    concept_id: str,
    learner_id: str,
    difficulty: Optional[str] = None,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Select and personalize a dialogue prompt based on learner profile and difficulty.

    Combines prompt selection logic with personalization to deliver interest-aligned
    questions that assess the same learning objectives.

    Args:
        concept_id: Concept identifier
        learner_id: Learner identifier
        difficulty: Desired difficulty level ("basic", "intermediate", "advanced")
        course_id: Course identifier (optional)

    Returns:
        Dictionary containing:
            - prompt: Personalized question string
            - prompt_id: Original prompt identifier
            - difficulty: Difficulty level
            - rubric: Assessment rubric
            - follow_up_if_good: List of follow-up questions
            - follow_up_if_developing: List of scaffolding questions

    Raises:
        FileNotFoundError: If learner or assessment not found
    """
    try:
        # Load learner model to get profile
        learner_model = load_learner_model(learner_id)
        learner_profile = learner_model.get("profile", {})

        # Load assessment data (try personalized version first, fallback to standard)
        try:
            concept_dir = config.get_concept_dir(concept_id, course_id)
            personalized_path = concept_dir / "assessments" / "dialogue-prompts-personalized.json"
            if personalized_path.exists():
                with open(personalized_path, "r", encoding="utf-8") as f:
                    assessment_data = json.load(f)
                logger.info("Loaded personalized assessment version")
            else:
                assessment_data = load_assessment(concept_id, "dialogue", course_id)
                logger.info("Loaded standard assessment version")
        except Exception as e:
            logger.warning(f"Could not load assessment: {e}")
            assessment_data = load_assessment(concept_id, "dialogue", course_id)

        # Filter prompts by difficulty if specified
        all_prompts = assessment_data.get("prompts", [])
        if difficulty:
            filtered_prompts = [p for p in all_prompts if p.get("difficulty") == difficulty]
            if not filtered_prompts:
                logger.warning(f"No prompts found for difficulty {difficulty}, using all prompts")
                filtered_prompts = all_prompts
        else:
            filtered_prompts = all_prompts

        if not filtered_prompts:
            raise ValueError(f"No dialogue prompts available for {concept_id}")

        # Select a random prompt
        selected_prompt = random.choice(filtered_prompts)

        # Personalize the prompt
        personalized_question = personalize_assessment_prompt(selected_prompt, learner_profile)

        # Return complete prompt data with personalized question
        return {
            "prompt": personalized_question,
            "prompt_id": selected_prompt.get("id"),
            "difficulty": selected_prompt.get("difficulty"),
            "learning_objective": selected_prompt.get("learning_objective", ""),
            "rubric": selected_prompt.get("rubric", {}),
            "follow_up_if_good": selected_prompt.get("follow_up_if_good", []),
            "follow_up_if_developing": selected_prompt.get("follow_up_if_developing", [])
        }

    except Exception as e:
        logger.error(f"Error selecting personalized dialogue prompt: {e}")
        raise


def select_personalized_teaching_moment(
    concept_id: str,
    learner_id: str,
    difficulty: Optional[str] = None,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Select and personalize a teaching moment assessment based on learner profile.

    Teaching moments are two-stage misconception correction activities where:
    1. Student responds to a character's misconception (Part 1)
    2. Character pushes back, student defends/clarifies (Part 2)
    3. Scoring based on combination of both responses

    Args:
        concept_id: Concept identifier
        learner_id: Learner identifier
        difficulty: Desired difficulty level ("basic", "intermediate", "advanced")
        course_id: Course identifier (optional)

    Returns:
        Dictionary containing personalized teaching moment with:
            - scenario: Character, situation, misconception
            - part1: Prompt and options
            - part2: Prompt, options, pushbacks
            - scoring: Combination-based rubric
            - teaching_moment_id: Original ID
            - difficulty: Difficulty level

    Raises:
        FileNotFoundError: If learner or teaching moments not found
    """
    try:
        # Load learner model to get profile
        learner_model = load_learner_model(learner_id)
        learner_profile = learner_model.get("profile", {})

        # Load teaching moment data (try personalized version first)
        try:
            concept_dir = config.get_concept_dir(concept_id, course_id)
            personalized_path = concept_dir / "assessments" / "teaching-moments-personalized.json"
            if personalized_path.exists():
                with open(personalized_path, "r", encoding="utf-8") as f:
                    tm_data = json.load(f)
                logger.info("Loaded personalized teaching moments")
            else:
                # Try standard version
                standard_path = concept_dir / "assessments" / "teaching-moments.json"
                if standard_path.exists():
                    with open(standard_path, "r", encoding="utf-8") as f:
                        tm_data = json.load(f)
                    logger.info("Loaded standard teaching moments")
                else:
                    raise FileNotFoundError(f"No teaching moments found for {concept_id}")
        except Exception as e:
            logger.warning(f"Could not load teaching moments: {e}")
            raise

        # Filter by difficulty if specified
        all_moments = tm_data.get("teaching_moments", [])
        if difficulty:
            filtered_moments = [m for m in all_moments if m.get("difficulty") == difficulty]
            if not filtered_moments:
                logger.warning(f"No teaching moments found for difficulty {difficulty}, using all")
                filtered_moments = all_moments
        else:
            filtered_moments = all_moments

        if not filtered_moments:
            raise ValueError(f"No teaching moments available for {concept_id}")

        # Select a random teaching moment
        selected_moment = random.choice(filtered_moments)

        # Personalize the scenario
        scenario_templates = selected_moment.get("scenario_templates", {})
        if scenario_templates:
            # Determine learner's interest category
            interests = learner_profile.get("interests", "")
            if isinstance(interests, list):
                interests = ", ".join(interests)
            interests = interests.lower()

            # Match interest to scenario
            if any(kw in interests for kw in ["history", "historical", "roman history", "inscriptions"]):
                scenario_key = "history"
            elif any(kw in interests for kw in ["archaeology", "archaeological", "excavation", "artifacts"]):
                scenario_key = "archaeology"
            elif any(kw in interests for kw in ["mythology", "mythological", "gods", "goddesses", "myths"]):
                scenario_key = "mythology"
            elif any(kw in interests for kw in ["literature", "literary", "poetry", "poems", "reading"]):
                scenario_key = "literature"
            else:
                scenario_key = "default"

            # Get personalized scenario
            if scenario_key in scenario_templates:
                selected_scenario = scenario_templates[scenario_key]
                logger.info(f"Personalized teaching moment using scenario: {scenario_key}")
            elif "default" in scenario_templates:
                selected_scenario = scenario_templates["default"]
                logger.info("Using default scenario template")
            else:
                # Fallback: use first available scenario
                selected_scenario = list(scenario_templates.values())[0]
                logger.info("Using first available scenario as fallback")
        else:
            # No templates, use base scenario
            selected_scenario = selected_moment.get("scenario", {})

        # Return complete teaching moment data with personalized scenario
        return {
            "type": "teaching-moment",  # Required for ContentRenderer switch
            "teaching_moment_id": selected_moment.get("id"),
            "difficulty": selected_moment.get("difficulty"),
            "learning_objective": selected_moment.get("learning_objective", ""),
            "scenario": selected_scenario,
            "part1": selected_moment.get("part1", {}),
            "part2": selected_moment.get("part2", {}),
            "scoring": selected_moment.get("scoring", {})
        }

    except Exception as e:
        logger.error(f"Error selecting personalized teaching moment: {e}")
        raise
