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

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


# ============================================================================
# Resource Loading Functions
# ============================================================================

def load_resource(concept_id: str, resource_type: str) -> Dict[str, Any]:
    """
    Load a resource from the resource bank.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        resource_type: Type of resource ("text-explainer" or "examples")

    Returns:
        Resource data as dictionary

    Raises:
        FileNotFoundError: If resource doesn't exist
        ValueError: If resource type is invalid
    """
    try:
        concept_dir = config.get_concept_dir(concept_id)

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


def load_assessment(concept_id: str, assessment_type: str) -> Dict[str, Any]:
    """
    Load an assessment from the resource bank.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")
        assessment_type: Type of assessment ("dialogue", "written", or "applied")

    Returns:
        Assessment data as dictionary

    Raises:
        FileNotFoundError: If assessment doesn't exist
        ValueError: If assessment type is invalid
    """
    try:
        concept_dir = config.get_concept_dir(concept_id)

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


def load_concept_metadata(concept_id: str) -> Dict[str, Any]:
    """
    Load metadata for a concept.

    Args:
        concept_id: Concept identifier (e.g., "concept-001")

    Returns:
        Metadata dictionary

    Raises:
        FileNotFoundError: If metadata doesn't exist
    """
    try:
        concept_dir = config.get_concept_dir(concept_id)
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
                "mastery_score": 0.0
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
        avg_score = sum(scores) / len(scores)
        num_assessments = len(assessments)

        # Check mastery criteria
        mastery_achieved = (
            avg_score >= config.MASTERY_THRESHOLD and
            num_assessments >= config.MIN_ASSESSMENTS_FOR_MASTERY
        )

        # Determine recommendation
        if mastery_achieved:
            recommendation = "progress"
            reason = f"Mastery achieved: {avg_score:.2f} average across {num_assessments} assessments"
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


def get_next_concept(current_concept_id: str) -> Optional[str]:
    """
    Determine the next concept in the learning path.

    Args:
        current_concept_id: Current concept ID (e.g., "concept-001")

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

            # Verify it exists in resource bank
            next_concept_dir = config.get_concept_dir(next_concept_id)
            if next_concept_dir.exists():
                logger.info(f"Next concept after {current_concept_id} is {next_concept_id}")
                return next_concept_id

        logger.info(f"No next concept after {current_concept_id}")
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
