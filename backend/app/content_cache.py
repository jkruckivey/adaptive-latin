"""
Content Cache Manager

Manages intelligent caching and retrieval of AI-generated content to reduce costs.
Implements a waterfall approach: pre-generated → cached → fresh generation.
"""

import sqlite3
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .config import config

logger = logging.getLogger(__name__)

# Database path
CACHE_DB_PATH = config.BASE_DIR / "content_cache.db"


def init_database():
    """Initialize the content cache database."""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        # Read and execute schema
        schema_file = Path(__file__).parent / "content_cache_schema.sql"
        with open(schema_file, 'r') as f:
            schema = f.read()

        cursor.executescript(schema)
        conn.commit()
        conn.close()

        logger.info(f"Content cache database initialized at {CACHE_DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing content cache database: {e}")
        raise


def cache_content(
    course_id: str,
    concept_id: str,
    content_type: str,
    tags: Dict[str, Any],
    content_data: Dict[str, Any],
    generated_by: str = "ai-cache"
) -> str:
    """
    Cache generated content for future reuse.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        content_type: Type of content ('explanation', 'question', 'feedback', etc.)
        tags: Dictionary of tags for retrieval (stage, learning_style, etc.)
        content_data: The actual content to cache
        generated_by: Source ('pre-gen', 'ai-cache', 'on-demand')

    Returns:
        content_id: UUID of cached content
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        content_id = str(uuid.uuid4())
        tags_json = json.dumps(tags, sort_keys=True)
        content_json = json.dumps(content_data)
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO content_cache
            (id, course_id, concept_id, content_type, tags, content_data,
             generated_by, created_at, last_used_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            content_id, course_id, concept_id, content_type,
            tags_json, content_json, generated_by, now, now
        ))

        conn.commit()
        conn.close()

        logger.info(f"Cached content: {content_type} for {concept_id} with tags {tags}")
        return content_id

    except Exception as e:
        logger.error(f"Error caching content: {e}")
        raise


def search_cache(
    course_id: str,
    concept_id: str,
    content_type: str,
    tags: Dict[str, Any],
    min_effectiveness: float = 0.6
) -> Optional[Dict[str, Any]]:
    """
    Search cache for matching content.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        content_type: Type of content
        tags: Tags to match
        min_effectiveness: Minimum effectiveness score (0.0-1.0)

    Returns:
        Cached content if found and effective, None otherwise
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        tags_json = json.dumps(tags, sort_keys=True)

        # Look for exact tag match with good effectiveness
        cursor.execute("""
            SELECT id, content_data, usage_count, effectiveness_score
            FROM content_cache
            WHERE course_id = ?
            AND concept_id = ?
            AND content_type = ?
            AND tags = ?
            AND effectiveness_score >= ?
            ORDER BY effectiveness_score DESC, usage_count DESC
            LIMIT 1
        """, (course_id, concept_id, content_type, tags_json, min_effectiveness))

        result = cursor.fetchone()

        if result:
            content_id, content_json, usage_count, effectiveness_score = result

            # Update last used and usage count
            cursor.execute("""
                UPDATE content_cache
                SET last_used_at = ?, usage_count = usage_count + 1
                WHERE id = ?
            """, (datetime.now().isoformat(), content_id))

            conn.commit()
            conn.close()

            logger.info(f"Cache HIT: {content_type} for {concept_id} (effectiveness: {effectiveness_score:.2f})")

            return {
                "id": content_id,
                "content": json.loads(content_json),
                "usage_count": usage_count + 1,
                "effectiveness_score": effectiveness_score,
                "source": "cache"
            }

        conn.close()
        logger.info(f"Cache MISS: {content_type} for {concept_id}")
        return None

    except Exception as e:
        logger.error(f"Error searching cache: {e}")
        return None


def track_content_usage(
    content_id: str,
    learner_id: str,
    learner_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track when content is shown to a learner.

    Args:
        content_id: ID of cached content
        learner_id: Learner identifier
        learner_context: Optional context about learner state

    Returns:
        usage_id: UUID of usage record
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        usage_id = str(uuid.uuid4())
        context_json = json.dumps(learner_context) if learner_context else None

        cursor.execute("""
            INSERT INTO content_usage
            (id, content_id, learner_id, learner_context, viewed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (usage_id, content_id, learner_id, context_json, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return usage_id

    except Exception as e:
        logger.error(f"Error tracking content usage: {e}")
        raise


def update_content_effectiveness(
    usage_id: str,
    was_effective: bool,
    learner_score: Optional[float] = None,
    time_to_mastery: Optional[float] = None
):
    """
    Update effectiveness after learner outcome is known.

    Args:
        usage_id: Usage record ID
        was_effective: Whether content led to successful learning
        learner_score: Score on next assessment
        time_to_mastery: Hours to reach mastery
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        # Update usage record
        cursor.execute("""
            UPDATE content_usage
            SET was_effective = ?,
                learner_score = ?,
                time_to_mastery = ?,
                outcome_determined_at = ?
            WHERE id = ?
        """, (
            1 if was_effective else 0,
            learner_score,
            time_to_mastery,
            datetime.now().isoformat(),
            usage_id
        ))

        # Get content_id to update cache effectiveness
        cursor.execute("SELECT content_id FROM content_usage WHERE id = ?", (usage_id,))
        result = cursor.fetchone()

        if result:
            content_id = result[0]

            # Recalculate effectiveness score for content
            cursor.execute("""
                SELECT
                    AVG(CASE WHEN was_effective = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                    COUNT(*) as total_measured
                FROM content_usage
                WHERE content_id = ? AND was_effective IS NOT NULL
            """, (content_id,))

            stats = cursor.fetchone()
            if stats and stats[1] > 0:  # Has measured outcomes
                success_rate, total_measured = stats

                # Weight by number of measurements (more data = more confidence)
                confidence = min(1.0, total_measured / 10.0)  # Full confidence after 10 uses
                effectiveness_score = (success_rate * confidence) + (0.5 * (1 - confidence))

                cursor.execute("""
                    UPDATE content_cache
                    SET effectiveness_score = ?,
                        success_count = (
                            SELECT COUNT(*) FROM content_usage
                            WHERE content_id = ? AND was_effective = 1
                        )
                    WHERE id = ?
                """, (effectiveness_score, content_id, content_id))

                logger.info(f"Updated content {content_id} effectiveness: {effectiveness_score:.2f}")

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Error updating content effectiveness: {e}")
        raise


def load_pregenerated_content(
    course_id: str,
    concept_id: str,
    content_type: str,
    learning_style: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Load pre-generated content from content library.

    Args:
        course_id: Course identifier
        concept_id: Concept identifier
        content_type: Type of content ('explanation', 'question', etc.)
        learning_style: Learning style for explanations

    Returns:
        Pre-generated content if available
    """
    try:
        from .config import config

        concept_dir = config.get_concept_dir(concept_id, course_id)
        content_library = concept_dir / "content-library"

        if content_type == "explanation" and learning_style:
            # Load pre-generated explanation
            explanation_file = content_library / "explanations" / f"{learning_style}.json"
            if explanation_file.exists():
                with open(explanation_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    logger.info(f"Loaded pre-generated {learning_style} explanation for {concept_id}")
                    return {
                        "content": content,
                        "source": "pre-generated"
                    }

        elif content_type == "question":
            # Load from question bank (random selection)
            # Implementation depends on question bank structure
            pass

        return None

    except Exception as e:
        logger.error(f"Error loading pre-generated content: {e}")
        return None


def get_cache_stats(course_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about cache usage and effectiveness.

    Args:
        course_id: Optional course filter

    Returns:
        Dictionary with cache statistics
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        where_clause = "WHERE course_id = ?" if course_id else ""
        params = (course_id,) if course_id else ()

        # Overall stats
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_cached,
                AVG(usage_count) as avg_usage,
                AVG(effectiveness_score) as avg_effectiveness,
                SUM(usage_count) as total_uses
            FROM content_cache
            {where_clause}
        """, params)

        stats = cursor.fetchone()

        # Cost savings estimate
        cursor.execute(f"""
            SELECT SUM(usage_count) FROM content_cache
            {where_clause}
        """, params)

        total_cache_hits = cursor.fetchone()[0] or 0
        estimated_cost_per_generation = 0.015  # $0.015 per AI call
        savings = total_cache_hits * estimated_cost_per_generation

        conn.close()

        return {
            "total_cached_items": stats[0] or 0,
            "average_usage_per_item": stats[1] or 0,
            "average_effectiveness": stats[2] or 0,
            "total_cache_hits": total_cache_hits,
            "estimated_cost_savings": f"${savings:.2f}"
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}
