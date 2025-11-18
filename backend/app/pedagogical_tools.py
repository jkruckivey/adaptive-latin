"""
Pedagogical Tools for AI Tutor

This module implements domain-agnostic tools for generating personalized educational content.
"""

import logging
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from .config import config
from .tools import load_concept_metadata

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

def generate_contextualized_example(
    concept_id: str,
    learner_interests: List[str],
    difficulty: str = "appropriate",
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an example illustrating a concept, tailored to the learner's interests.

    Args:
        concept_id: ID of the concept to illustrate
        learner_interests: List of learner interests (e.g., ["sci-fi", "cooking"])
        difficulty: "easier", "appropriate", or "harder"
        course_id: Optional course ID

    Returns:
        Dict containing the generated example and explanation
    """
    try:
        # Load concept metadata
        metadata = load_concept_metadata(concept_id, course_id)
        concept_title = metadata.get("title", concept_id)
        concept_desc = metadata.get("description", "")
        
        # Format interests
        interests_str = ", ".join(learner_interests) if learner_interests else "general topics"
        
        # Build prompt
        prompt = (
            f"Generate a contextualized example to teach the concept: '{concept_title}'.\n"
            f"Concept Description: {concept_desc}\n\n"
            f"Learner Interests: {interests_str}\n"
            f"Difficulty: {difficulty}\n\n"
            f"Instructions:\n"
            f"1. Create a concrete example (sentence, problem, or scenario) that demonstrates this concept.\n"
            f"2. Use vocabulary and context related to the learner's interests.\n"
            f"3. Provide a clear explanation of how the concept applies in this specific example.\n"
            f"4. Ensure the example is factually correct for the subject matter.\n\n"
            f"Respond with a JSON object containing:\n"
            f"- 'example': The example text/problem\n"
            f"- 'explanation': The explanation connecting the example to the concept\n"
            f"- 'context_used': Which interest was used"
        )

        # Call Claude
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0.7,
            system="You are an expert tutor who creates personalized learning examples.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response (assuming Claude returns JSON-like text, might need robust parsing)
        # For simplicity in this prototype, we'll assume the prompt works or use a helper if needed.
        # In a real app, we'd use a structured output parser or function calling.
        import json
        import re
        
        content = response.content[0].text
        # Extract JSON block if present
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            # Fallback if no JSON found
            return {
                "example": content,
                "explanation": "Generated explanation",
                "context_used": interests_str
            }

    except Exception as e:
        logger.error(f"Error generating contextualized example: {e}")
        return {
            "example": "Error generating example.",
            "explanation": str(e),
            "context_used": "none"
        }

def break_down_concept_application(
    concept_id: str,
    student_work: Optional[str] = None,
    problem_statement: Optional[str] = None,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deconstructs a complex application of a concept into steps.

    Args:
        concept_id: ID of the concept
        student_work: The student's attempt or question (optional)
        problem_statement: The problem being solved (optional)
        course_id: Optional course ID

    Returns:
        Dict containing the breakdown steps
    """
    try:
        # Load concept metadata
        metadata = load_concept_metadata(concept_id, course_id)
        concept_title = metadata.get("title", concept_id)
        
        # Build prompt
        context_str = ""
        if problem_statement:
            context_str += f"Problem: {problem_statement}\n"
        if student_work:
            context_str += f"Student's Work: {student_work}\n"
            
        prompt = (
            f"Break down the application of the concept '{concept_title}' into clear steps.\n"
            f"{context_str}\n"
            f"Instructions:\n"
            f"1. Identify the key steps required to apply this concept correctly.\n"
            f"2. If student work is provided, analyze where they might have missed a step.\n"
            f"3. If no work is provided, generate a generic worked example.\n"
            f"4. Output a list of steps with explanations.\n\n"
            f"Respond with a JSON object containing:\n"
            f"- 'steps': List of objects with 'step_number', 'action', 'explanation'\n"
            f"- 'analysis': specific feedback on student work (if provided)"
        )

        # Call Claude
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0.5,
            system="You are an expert tutor who breaks down complex concepts.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        import re
        content = response.content[0].text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"steps": [], "analysis": content}

    except Exception as e:
        logger.error(f"Error breaking down concept: {e}")
        return {"steps": [], "analysis": f"Error: {str(e)}"}

def compare_concepts(
    concept_id_a: str,
    concept_id_b: str,
    course_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a comparison matrix between two concepts.

    Args:
        concept_id_a: First concept ID
        concept_id_b: Second concept ID
        course_id: Optional course ID

    Returns:
        Dict containing the comparison table data
    """
    try:
        # Load metadata
        meta_a = load_concept_metadata(concept_id_a, course_id)
        meta_b = load_concept_metadata(concept_id_b, course_id)
        
        title_a = meta_a.get("title", concept_id_a)
        title_b = meta_b.get("title", concept_id_b)
        
        prompt = (
            f"Compare and contrast these two concepts:\n"
            f"1. {title_a}: {meta_a.get('description', '')}\n"
            f"2. {title_b}: {meta_b.get('description', '')}\n\n"
            f"Instructions:\n"
            f"1. Identify the key dimensions of comparison (e.g., usage, form, meaning).\n"
            f"2. Create a comparison table.\n"
            f"3. Highlight the most common confusion point.\n\n"
            f"Respond with a JSON object containing:\n"
            f"- 'comparison_points': List of objects with 'dimension', 'concept_a_val', 'concept_b_val'\n"
            f"- 'key_difference': Summary of the main distinction"
        )

        # Call Claude
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0.5,
            system="You are an expert tutor who clarifies confusing concepts.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        import re
        content = response.content[0].text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"comparison_points": [], "key_difference": content}

    except Exception as e:
        logger.error(f"Error comparing concepts: {e}")
        return {"comparison_points": [], "key_difference": f"Error: {str(e)}"}
