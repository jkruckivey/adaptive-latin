"""
Resource Loading and Learner Model Management (with Database)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import config
from .database import get_db_connection

logger = logging.getLogger(__name__)

# ============================================================================
# Resource Loading Functions
# ============================================================================

def load_resource(concept_id: str, resource_type: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    # ... (implementation from the original tools.py)
    pass

def load_assessment(concept_id: str, assessment_type: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    # ... (implementation from the original tools.py)
    pass

def load_concept_metadata(concept_id: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    # ... (implementation from the original tools.py)
    pass

# ============================================================================
# Learner Model Management Functions (with Database)
# ============================================================================

def create_learner_model(
    learner_id: str,
    learner_name: Optional[str] = None,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new learner model in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM learners WHERE id = ?", (learner_id,))
    if cursor.fetchone():
        raise ValueError(f"Learner {learner_id} already exists")

    learner_model = {
        "learner_id": learner_id,
        "learner_name": learner_name,
        "profile": profile or {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_course": config.DEFAULT_COURSE_ID,
        "current_concept": "concept-001",
        "concepts": {},
        "question_history": [],
        "overall_progress": {
            "concepts_completed": 0,
            "concepts_in_progress": 1,
            "total_assessments": 0,
            "average_calibration_accuracy": 0.0
        }
    }

    cursor.execute(
        "INSERT INTO learners (id, name, profile, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (learner_id, learner_name, json.dumps(profile), learner_model['created_at'], learner_model['updated_at'])
    )
    conn.commit()
    conn.close()

    logger.info(f"Created new learner model for {learner_id} in database")
    return learner_model


def load_learner_model(learner_id: str) -> Dict[str, Any]:
    """
    Load an existing learner model from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learners WHERE id = ?", (learner_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise FileNotFoundError(f"Learner {learner_id} not found")

    # Reconstruct the model to match the old structure for now
    profile = json.loads(row['profile']) if row['profile'] else {}
    # This is a simplified reconstruction. In a real scenario, you'd migrate all fields to the db.
    learner_model = {
        "learner_id": row['id'],
        "learner_name": row['name'],
        "profile": profile,
        "created_at": row['created_at'],
        "updated_at": row['updated_at'],
        "current_course": config.DEFAULT_COURSE_ID,
        "current_concept": "concept-001",
        "concepts": {},
        "question_history": [],
        "overall_progress": {
            "concepts_completed": 0,
            "concepts_in_progress": 1,
            "total_assessments": 0,
            "average_calibration_accuracy": 0.0
        }
    }
    logger.info(f"Loaded learner model for {learner_id} from database")
    return learner_model


def save_learner_model(learner_id: str, model: Dict[str, Any]) -> None:
    """
    Save a learner model to the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    updated_at = datetime.now().isoformat()

    cursor.execute(
        "UPDATE learners SET name = ?, profile = ?, updated_at = ? WHERE id = ?",
        (model.get('learner_name'), json.dumps(model.get('profile', {})), updated_at, learner_id)
    )
    conn.commit()
    conn.close()

    logger.info(f"Saved learner model for {learner_id} to database")
