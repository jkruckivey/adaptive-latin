"""
API Routers for Concept-related endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from ..schemas import ConceptResponse
from ..tools import load_concept_metadata, list_all_concepts
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/concept/{concept_id}", response_model=ConceptResponse)
async def get_concept_info(concept_id: str):
    """
    Get information about a specific concept.
    """
    try:
        metadata = load_concept_metadata(concept_id)
        return {
            "concept_id": metadata["id"],
            "title": metadata["title"],
            "difficulty": metadata["difficulty"],
            "prerequisites": metadata["prerequisites"],
            "learning_objectives": metadata["learning_objectives"],
            "estimated_mastery_time": metadata["estimated_mastery_time"],
            "vocabulary": metadata.get("vocabulary", [])
        }
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Concept not found: {concept_id}")
    except Exception as e:
        logger.error(f"Error getting concept info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get concept info: {str(e)}")


@router.get("/concepts")
async def list_concepts_endpoint():
    """
    List all available concepts.
    """
    try:
        concepts = list_all_concepts()
        return {
            "success": True,
            "concepts": concepts,
            "total": len(concepts)
        }
    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list concepts: {str(e)}")
