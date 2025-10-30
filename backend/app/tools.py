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
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new learner model with initial state.

    Args:
        learner_id: Unique identifier for the learner
        learner_name: Learner's name (optional)
        profile: Learner profile from onboarding (optional)

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
        learner_model = {
            "learner_id": learner_id,
            "learner_name": learner_name,
            "profile": profile or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_course": config.DEFAULT_COURSE_ID,  # Support for multiple courses
            "current_concept": "concept-001",
            "concepts": {},
            "question_history": [],  # Track recent questions to avoid repetition
            "overall_progress": {
                "concepts_completed": 0,
                "concepts_in_progress": 1,
                "total_assessments": 0,
                "average_calibration_accuracy": 0.0
            }
        }

        # Save to disk
        save_learner_model(learner_id, learner_model)

        logger.info(f"Created new learner model for {learner_id}")
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
        model = load_learner_model(learner_id)

        # Initialize concept tracking if not exists
        if concept_id not in model["concepts"]:
            model["concepts"][concept_id] = {
                "concept_id": concept_id,
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "assessments": [],
                "confidence_history": [],
                "mastery_score": 0.0,
                "review_data": initialize_review_data(concept_id)
            }

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

        # Save updated model
        save_learner_model(learner_id, model)

        logger.info(f"Updated learner model for {learner_id}, concept {concept_id}")
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
) -> Dict[str, Any]:
    """Record an assessment attempt and determine mastery completion.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Concept currently being practiced
        is_correct: Whether the learner's answer was correct
        confidence: Self-reported confidence rating (1-5) or None
        question_type: Type of question answered (multiple-choice, fill-blank, dialogue)

    Returns:
        Dictionary with mastery tracking details including updated mastery score,
        assessment count, completion flag, and total concepts completed.
    """

    try:
        # Translate correctness into a mastery score contribution
        score = 1.0 if is_correct else 0.0

        # Build assessment payload for the learner model helper
        assessment_data: Dict[str, Any] = {
            "type": question_type or "assessment",
            "score": score,
            "self_confidence": confidence,
        }

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

        # Calculate metrics
        scores = [a["score"] for a in assessments]
        num_assessments = len(assessments)

        # Use sliding window for mastery calculation (recent performance matters most)
        # This allows learners to recover from early mistakes
        window_size = config.MASTERY_WINDOW_SIZE
        recent_scores = scores[-window_size:] if len(scores) > window_size else scores
        avg_score = sum(recent_scores) / len(recent_scores)

        logger.info(f"Mastery calculation for {concept_id}: {len(recent_scores)} recent assessments, avg={avg_score:.2f}")

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


def list_all_concepts() -> List[str]:
    """
    Get a list of all available concepts.

    Returns:
        List of concept IDs
    """
    try:
        concepts = []
        for concept_dir in config.RESOURCE_BANK_DIR.iterdir():
            if concept_dir.is_dir() and concept_dir.name.startswith("concept-"):
                concepts.append(concept_dir.name)

        concepts.sort()
        logger.info(f"Found {len(concepts)} concepts")
        return concepts

    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        return []


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
                "visual": ["visual_learners", "video"],
                "connections": ["conceptual_learners", "article"],
                "practice": ["kinesthetic_learners", "practice"]
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
