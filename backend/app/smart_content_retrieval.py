"""
Smart Content Retrieval

Implements waterfall approach for content delivery:
1. Try pre-generated library (FREE)
2. Try cache (FREE)
3. Generate fresh with AI (COSTS $$$)

This module optimizes costs while maintaining personalization.
"""

import logging
from typing import Dict, Any, Optional
from .content_cache import (
    load_pregenerated_content,
    search_cache,
    cache_content,
    track_content_usage
)
from .agent import generate_content

logger = logging.getLogger(__name__)


def get_smart_content(
    learner_id: str,
    concept_id: str,
    course_id: str,
    stage: str,
    learning_style: str,
    correctness: Optional[bool] = None,
    confidence: Optional[int] = None,
    remediation_type: Optional[str] = None,
    question_context: Optional[Dict[str, Any]] = None,
    force_fresh: bool = False
) -> Dict[str, Any]:
    """
    Retrieve content using smart waterfall approach.

    This is the main entry point for getting learning content. It tries:
    1. Pre-generated content (instant, free)
    2. Cached content (instant, free)
    3. Fresh AI generation (slow, expensive)

    Args:
        learner_id: Learner identifier
        concept_id: Concept identifier
        course_id: Course identifier
        stage: Learning stage ("start", "practice", "assess", etc.)
        learning_style: Learner's preferred style
        correctness: Whether previous answer was correct
        confidence: Confidence level 1-4
        remediation_type: Type of remediation if needed
        question_context: Context about current question
        force_fresh: If True, skip cache and generate fresh

    Returns:
        Dictionary with content and metadata about source
    """

    # Build tags for cache lookup
    tags = {
        "stage": stage,
        "learning_style": learning_style
    }

    if correctness is not None:
        tags["correctness"] = correctness
    if confidence is not None:
        tags["confidence"] = confidence
    if remediation_type:
        tags["remediation_type"] = remediation_type

    content_type = _determine_content_type(stage, correctness)

    logger.info(f"Smart content request: {concept_id}, {content_type}, tags={tags}")

    # ===========================================================================
    # STEP 1: Try pre-generated content (FREE, INSTANT)
    # ===========================================================================
    if not force_fresh and stage == "start":
        logger.info("→ Trying pre-generated content...")

        pregenerated = load_pregenerated_content(
            course_id=course_id,
            concept_id=concept_id,
            content_type=content_type,
            learning_style=learning_style
        )

        if pregenerated:
            logger.info("✓ Using PRE-GENERATED content (FREE)")
            return {
                "success": True,
                "content": pregenerated["content"],
                "source": "pre-generated",
                "cost": 0.0
            }

    # ===========================================================================
    # STEP 2: Try cached content (FREE, INSTANT)
    # ===========================================================================
    if not force_fresh:
        logger.info("→ Searching cache...")

        cached = search_cache(
            course_id=course_id,
            concept_id=concept_id,
            content_type=content_type,
            tags=tags,
            min_effectiveness=0.7  # Only reuse if 70%+ effective
        )

        if cached:
            # Track usage
            usage_id = track_content_usage(
                content_id=cached["id"],
                learner_id=learner_id,
                learner_context={
                    "stage": stage,
                    "learning_style": learning_style,
                    "concept_id": concept_id
                }
            )

            logger.info(f"✓ Using CACHED content (FREE, effectiveness: {cached['effectiveness_score']:.2f})")
            return {
                "success": True,
                "content": cached["content"],
                "source": "cache",
                "usage_id": usage_id,  # Track for effectiveness updates
                "effectiveness_score": cached["effectiveness_score"],
                "cost": 0.0
            }

    # ===========================================================================
    # STEP 3: Generate fresh content with AI (COSTS $$$)
    # ===========================================================================
    logger.info("→ Generating fresh content with AI...")

    result = generate_content(
        learner_id=learner_id,
        stage=stage,
        correctness=correctness,
        confidence=confidence,
        remediation_type=remediation_type,
        question_context=question_context
    )

    if not result.get("success"):
        logger.error("✗ Failed to generate content")
        return result

    content = result.get("content")

    # Cache the freshly generated content for future use
    try:
        content_id = cache_content(
            course_id=course_id,
            concept_id=concept_id,
            content_type=content_type,
            tags=tags,
            content_data=content,
            generated_by="ai-cache"
        )

        # Track usage
        usage_id = track_content_usage(
            content_id=content_id,
            learner_id=learner_id,
            learner_context={
                "stage": stage,
                "learning_style": learning_style,
                "concept_id": concept_id
            }
        )

        logger.info(f"✓ Generated FRESH content and cached it (COST: ~$0.015)")
        return {
            "success": True,
            "content": content,
            "source": "fresh-ai",
            "usage_id": usage_id,
            "cached_as": content_id,
            "cost": 0.015  # Estimated cost per generation
        }

    except Exception as e:
        logger.error(f"Failed to cache fresh content: {e}")
        # Still return the content even if caching failed
        return {
            "success": True,
            "content": content,
            "source": "fresh-ai",
            "cost": 0.015
        }


def _determine_content_type(stage: str, correctness: Optional[bool]) -> str:
    """
    Determine content type based on stage and correctness.

    Args:
        stage: Learning stage
        correctness: Whether answer was correct

    Returns:
        Content type string
    """
    if stage == "start":
        return "explanation"
    elif stage == "assess":
        return "question"
    elif stage == "remediate":
        return "remediation"
    elif correctness is not None:
        return "feedback"
    else:
        return "content"


def get_content_stats_for_learner(learner_id: str) -> Dict[str, Any]:
    """
    Get statistics about content delivery for a specific learner.

    Args:
        learner_id: Learner identifier

    Returns:
        Dictionary with learner-specific stats
    """
    # This would query content_usage table for learner-specific stats
    # Implementation depends on how detailed you want the tracking
    return {
        "learner_id": learner_id,
        "total_content_delivered": 0,
        "from_cache_percentage": 0.0,
        "estimated_cost_savings": 0.0
    }
