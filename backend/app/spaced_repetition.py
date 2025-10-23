"""
Spaced Repetition System for Long-Term Retention

Implements simplified SM-2 algorithm for calculating optimal review intervals
based on learner performance and mastery.

Key concepts:
- Interval: Days until next review
- Ease Factor (EF): Multiplier for interval growth (starts at 2.5)
- Repetitions: Number of successful reviews in a row

Algorithm:
1. First review: 1 day
2. Second review: 6 days
3. Subsequent reviews: previous_interval × ease_factor
4. Ease factor adjusts based on performance (quality rating 0-5)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


def calculate_quality_rating(score: float, confidence_error: int) -> int:
    """
    Convert assessment score and confidence calibration into SM-2 quality rating (0-5).

    Quality ratings:
    5 = Perfect (score >= 0.9, well calibrated)
    4 = Good (score >= 0.8, reasonably calibrated)
    3 = Passing (score >= 0.7)
    2 = Difficult (score >= 0.6)
    1 = Poor (score >= 0.5)
    0 = Failed (score < 0.5)

    Args:
        score: Assessment score (0.0-1.0)
        confidence_error: Calibration error from confidence tracking

    Returns:
        Quality rating 0-5
    """
    # Base rating on score
    if score >= 0.9:
        base_rating = 5
    elif score >= 0.8:
        base_rating = 4
    elif score >= 0.7:
        base_rating = 3
    elif score >= 0.6:
        base_rating = 2
    elif score >= 0.5:
        base_rating = 1
    else:
        base_rating = 0

    # Adjust down for severe miscalibration (overconfidence is worse for retention)
    if confidence_error >= 3:  # Severely overconfident
        base_rating = max(0, base_rating - 1)

    return base_rating


def calculate_next_review(
    current_interval: int,
    repetitions: int,
    ease_factor: float,
    quality: int
) -> Tuple[int, int, float]:
    """
    Calculate next review interval using modified SM-2 algorithm.

    Args:
        current_interval: Current interval in days
        repetitions: Number of successful reviews in a row
        ease_factor: Current ease factor (typically 1.3-2.5)
        quality: Quality rating of current review (0-5)

    Returns:
        Tuple of (next_interval_days, new_repetitions, new_ease_factor)
    """
    # Update ease factor based on quality
    # EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Clamp ease factor between 1.3 and 2.5
    new_ef = max(1.3, min(2.5, new_ef))

    # If quality < 3, reset repetitions (concept needs to be relearned)
    if quality < 3:
        new_repetitions = 0
        next_interval = 1  # Review tomorrow
    else:
        new_repetitions = repetitions + 1

        # Calculate interval based on repetition number
        if new_repetitions == 1:
            next_interval = 1  # First successful review: 1 day
        elif new_repetitions == 2:
            next_interval = 6  # Second successful review: 6 days
        else:
            # Subsequent reviews: multiply by ease factor
            next_interval = math.ceil(current_interval * new_ef)

    logger.info(f"SM-2 calculation: quality={quality}, EF={ease_factor:.2f}→{new_ef:.2f}, "
                f"reps={repetitions}→{new_repetitions}, interval={current_interval}→{next_interval} days")

    return next_interval, new_repetitions, new_ef


def initialize_review_data(concept_id: str) -> Dict:
    """
    Initialize spaced repetition data for a new concept.

    Args:
        concept_id: The concept identifier

    Returns:
        Initial review data dictionary
    """
    return {
        "concept_id": concept_id,
        "interval": 1,  # Start with 1-day interval
        "repetitions": 0,
        "ease_factor": 2.5,  # Default ease factor
        "last_reviewed": None,
        "next_review": None,
        "review_history": []
    }


def update_review_schedule(
    review_data: Dict,
    score: float,
    confidence_error: int = 0
) -> Dict:
    """
    Update review schedule after an assessment.

    Args:
        review_data: Current review data for the concept
        score: Assessment score (0.0-1.0)
        confidence_error: Calibration error (-5 to +5)

    Returns:
        Updated review data
    """
    # Calculate quality rating from performance
    quality = calculate_quality_rating(score, confidence_error)

    # Calculate next review interval
    next_interval, new_reps, new_ef = calculate_next_review(
        current_interval=review_data.get("interval", 1),
        repetitions=review_data.get("repetitions", 0),
        ease_factor=review_data.get("ease_factor", 2.5),
        quality=quality
    )

    # Update review data
    now = datetime.now()
    next_review_date = now + timedelta(days=next_interval)

    review_data.update({
        "interval": next_interval,
        "repetitions": new_reps,
        "ease_factor": new_ef,
        "last_reviewed": now.isoformat(),
        "next_review": next_review_date.isoformat(),
    })

    # Add to review history
    if "review_history" not in review_data:
        review_data["review_history"] = []

    review_data["review_history"].append({
        "timestamp": now.isoformat(),
        "score": score,
        "quality": quality,
        "interval": next_interval,
        "ease_factor": new_ef
    })

    logger.info(f"Review scheduled: {review_data['concept_id']} - next review in {next_interval} days "
                f"({next_review_date.strftime('%Y-%m-%d')})")

    return review_data


def get_due_reviews(learner_model: Dict, include_upcoming: int = 0) -> List[Dict]:
    """
    Get concepts that are due for review.

    Args:
        learner_model: The learner's model containing concept data
        include_upcoming: Include concepts due within N days (default 0 = today only)

    Returns:
        List of concepts due for review, sorted by priority
    """
    due_concepts = []
    now = datetime.now()

    for concept_id, concept_data in learner_model.get("concepts", {}).items():
        # Skip concepts that haven't been started or have no review data
        if "review_data" not in concept_data:
            continue

        review_data = concept_data["review_data"]

        # Check if review is due
        if review_data.get("next_review"):
            next_review = datetime.fromisoformat(review_data["next_review"])
            days_until_due = (next_review - now).days

            if days_until_due <= include_upcoming:
                # Calculate priority (more overdue = higher priority)
                days_overdue = -days_until_due if days_until_due < 0 else 0

                due_concepts.append({
                    "concept_id": concept_id,
                    "next_review": review_data["next_review"],
                    "days_overdue": days_overdue,
                    "days_until_due": days_until_due,
                    "interval": review_data.get("interval", 1),
                    "repetitions": review_data.get("repetitions", 0),
                    "ease_factor": review_data.get("ease_factor", 2.5),
                    "mastery_score": concept_data.get("mastery_score", 0.0)
                })

    # Sort by priority: overdue first, then by next review date
    due_concepts.sort(key=lambda x: (x["days_until_due"], x["concept_id"]))

    logger.info(f"Found {len(due_concepts)} concepts due for review (include_upcoming={include_upcoming})")

    return due_concepts


def get_review_stats(learner_model: Dict) -> Dict:
    """
    Get overall statistics about spaced repetition progress.

    Args:
        learner_model: The learner's model

    Returns:
        Dictionary with review statistics
    """
    concepts = learner_model.get("concepts", {})
    total_concepts = len(concepts)

    concepts_with_reviews = 0
    total_reviews = 0
    due_today = 0
    due_this_week = 0

    now = datetime.now()

    for concept_data in concepts.values():
        if "review_data" in concept_data:
            concepts_with_reviews += 1
            review_data = concept_data["review_data"]

            # Count total reviews from history
            total_reviews += len(review_data.get("review_history", []))

            # Check if due
            if review_data.get("next_review"):
                next_review = datetime.fromisoformat(review_data["next_review"])
                days_until_due = (next_review - now).days

                if days_until_due <= 0:
                    due_today += 1
                elif days_until_due <= 7:
                    due_this_week += 1

    return {
        "total_concepts": total_concepts,
        "concepts_with_reviews": concepts_with_reviews,
        "total_reviews_completed": total_reviews,
        "due_today": due_today,
        "due_this_week": due_this_week,
        "average_reviews_per_concept": total_reviews / concepts_with_reviews if concepts_with_reviews > 0 else 0
    }
