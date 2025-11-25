"""
Claude API Integration with Tool Use

This module handles interaction with Claude API, including tool definitions,
system prompt management, and conversation handling.
"""

import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from anthropic import Anthropic
from .config import config
from .constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_API_TIMEOUT_SECONDS,
    RETRY_BACKOFF_BASE,
    RECENT_QUESTIONS_DISPLAY_COUNT,
    MAX_QUESTIONS_IN_HISTORY,
    CUMULATIVE_REVIEW_CONCEPTS_COUNT,
    MAX_EXTERNAL_RESOURCES_TO_ATTACH,
    STAGE_PREVIEW,
    STAGE_START,
    STAGE_PRACTICE,
    STAGE_ASSESS,
    STAGE_REMEDIATE,
    STAGE_REINFORCE
)
from .content_generators import (
    generate_preview_request,
    generate_diagnostic_request,
    generate_practice_request,
    generate_remediation_request,
    generate_reinforcement_request
)
from .tools import (
    load_resource,
    load_assessment,
    load_concept_metadata,
    update_learner_model,
    calculate_mastery,
    get_next_concept,
    load_learner_model,
    should_show_cumulative_review,
    select_concepts_for_cumulative,
    select_question_difficulty,
    detect_struggle
)
from .confidence import (
    calculate_calibration,
    get_calibration_feedback,
    should_intervene_on_confidence,
    get_calibration_pattern_feedback,
    calculate_overall_calibration
)
from .pedagogical_tools import (
    generate_contextualized_example,
    break_down_concept_application,
    compare_concepts
)

logger = logging.getLogger(__name__)


def validate_diagnostic_content(content_obj: Dict) -> Tuple[bool, str]:
    """
    Validate diagnostic question content for structural integrity.

    Checks:
    - Multiple-choice: has exactly one correct answer, valid index, unique options
    - Fill-blank: has correct answers matching number of blanks
    - Dialogue: has question text

    Args:
        content_obj: The parsed JSON content object

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    content_type = content_obj.get('type', '')

    if content_type == 'multiple-choice':
        # Validate multiple-choice question
        if 'correctAnswer' not in content_obj:
            return False, "Multiple-choice question missing 'correctAnswer' field"

        correct_answer = content_obj['correctAnswer']
        if not isinstance(correct_answer, int):
            return False, f"correctAnswer must be an integer, got {type(correct_answer).__name__}"

        options = content_obj.get('options', [])
        if not options:
            return False, "Multiple-choice question missing 'options' array"

        if correct_answer < 0 or correct_answer >= len(options):
            return False, f"correctAnswer index {correct_answer} out of bounds for {len(options)} options"

        # Check for duplicate options
        unique_options = set(options)
        if len(unique_options) < len(options):
            return False, "Multiple-choice question has duplicate options"

        # Ensure scenario and question exist
        if 'scenario' not in content_obj or not content_obj['scenario']:
            return False, "Multiple-choice question missing 'scenario' field (required for authentic context)"

        if 'question' not in content_obj or not content_obj['question']:
            return False, "Multiple-choice question missing 'question' field"

        logger.info(f"✓ Valid multiple-choice: {len(options)} unique options, correctAnswer={correct_answer}")
        return True, ""

    elif content_type == 'fill-blank':
        # Validate fill-blank exercise
        if 'correctAnswers' not in content_obj:
            return False, "Fill-blank exercise missing 'correctAnswers' field"

        correct_answers = content_obj['correctAnswers']
        if not isinstance(correct_answers, list):
            return False, f"correctAnswers must be a list, got {type(correct_answers).__name__}"

        blanks = content_obj.get('blanks', [])
        if not blanks:
            return False, "Fill-blank exercise missing 'blanks' array"

        if len(correct_answers) != len(blanks):
            return False, f"Fill-blank has {len(blanks)} blanks but {len(correct_answers)} correctAnswers"

        # Ensure sentence exists
        if 'sentence' not in content_obj or not content_obj['sentence']:
            return False, "Fill-blank exercise missing 'sentence' field"

        logger.info(f"✓ Valid fill-blank: {len(blanks)} blanks with matching answers")
        return True, ""

    elif content_type == 'dialogue':
        # Validate dialogue question
        if 'question' not in content_obj or not content_obj['question']:
            return False, "Dialogue question missing 'question' field"

        logger.info(f"✓ Valid dialogue question")
        return True, ""

    # Non-diagnostic content types don't need validation
    return True, ""


def strip_video_content(content_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove any video resources from content object.

    This is a hard enforcement to prevent videos from appearing,
    regardless of what the AI generates.

    Args:
        content_obj: The content object to clean

    Returns:
        Content object with videos removed
    """
    if 'external_resources' in content_obj and content_obj['external_resources']:
        # Filter out any resources with type: "video"
        original_count = len(content_obj['external_resources'])
        content_obj['external_resources'] = [
            res for res in content_obj['external_resources']
            if res.get('type') != 'video'
        ]
        removed_count = original_count - len(content_obj['external_resources'])

        if removed_count > 0:
            logger.info(f"🚫 Stripped {removed_count} video resource(s) from content")

        # If no resources left, remove the field entirely
        if not content_obj['external_resources']:
            del content_obj['external_resources']

    return content_obj


def evaluate_dialogue_response(question: str, context: str, student_answer: str, concept_id: str, exchange_count: int = 0) -> Dict[str, Any]:
    """
    Evaluate an open-ended dialogue response using Claude AI with rubric-based feedback.
    For multi-turn dialogues, also generates a follow-up question.

    Args:
        question: The dialogue question asked
        context: The scenario/context for the question
        student_answer: The student's open-ended response
        concept_id: The concept being assessed
        exchange_count: Number of previous exchanges (for multi-turn dialogue)

    Returns:
        Dict with:
        - is_correct (bool): Whether answer demonstrates understanding
        - feedback (str): Brief conversational feedback (1-2 sentences)
        - score (float): Score from 0.0 to 1.0
        - followUpQuestion (str): Next question to continue the dialogue
        - dialogueComplete (bool): Whether dialogue should end
    """
    try:
        # Check for empty or very short responses first
        if not student_answer or len(student_answer.strip()) < 5:
            return {
                "is_correct": False,
                "feedback": "Can you tell me more? Even a brief explanation helps me understand your thinking.",
                "score": 0.1,
                "followUpQuestion": question,  # Repeat the question
                "dialogueComplete": False
            }

        # Build evaluation prompt for Claude - optimized for quick back-and-forth
        evaluation_prompt = f"""You are a Socratic tutor having a quick back-and-forth dialogue about Latin grammar.
This is exchange #{exchange_count + 1} of an ongoing conversation.

QUESTION ASKED:
{question}

CONTEXT:
{context if context else "(General Latin grammar discussion)"}

STUDENT'S RESPONSE:
{student_answer}

YOUR TASK:
1. Give brief, encouraging feedback (1 sentence max)
2. Generate a natural follow-up question that builds on their answer
3. Keep the dialogue flowing conversationally

GUIDELINES:
- Feedback should be SHORT and conversational (like texting, not an essay)
- If they're right: acknowledge briefly, then dig deeper
- If they're partially right: gently guide toward the gap
- If they're wrong: redirect with a hint, don't lecture
- Follow-up questions should be SPECIFIC and QUICK to answer

Respond with ONLY a JSON object (no markdown):
{{"score": 0.75, "is_correct": true, "feedback": "Exactly right!", "followUpQuestion": "Now, what happens to that ending in the plural?"}}

Score >= 0.5 means partial understanding. Keep everything SHORT and conversational."""

        # Use a smaller model for faster evaluation
        from anthropic import Anthropic
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Use Haiku for fast evaluation
            max_tokens=300,
            timeout=15,
            messages=[{
                "role": "user",
                "content": evaluation_prompt
            }]
        )

        # Parse the response
        response_text = response.content[0].text.strip()
        logger.info(f"Dialogue evaluation response: {response_text[:200]}")

        # Try to parse as JSON
        import json
        try:
            # Remove any markdown code fences if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            score = float(result.get("score", 0.5))
            is_correct = result.get("is_correct", score >= 0.5)
            feedback = result.get("feedback", "Thank you for your thoughtful response.")
            follow_up = result.get("followUpQuestion", "")

            # Clamp score to valid range
            score = max(0.0, min(1.0, score))

            # Determine if dialogue should complete
            # Complete if: high score after 2+ exchanges, or 3 exchanges reached
            should_complete = (exchange_count >= 2 and score >= 0.85) or exchange_count >= 2

            return {
                "is_correct": is_correct,
                "feedback": feedback,
                "score": score,
                "followUpQuestion": follow_up if not should_complete else "",
                "dialogueComplete": should_complete
            }

        except json.JSONDecodeError:
            # If JSON parsing fails, extract feedback from plain text
            logger.warning(f"Failed to parse dialogue evaluation as JSON: {response_text[:100]}")
            return {
                "is_correct": True,
                "feedback": "Thank you for your explanation. Your response shows you're engaging with the material.",
                "score": 0.6,
                "followUpQuestion": "Can you tell me more about how you arrived at that understanding?",
                "dialogueComplete": False
            }

    except Exception as e:
        logger.error(f"Error evaluating dialogue response: {e}")
        # Default to neutral evaluation on error
        return {
            "is_correct": True,
            "feedback": "Thank you for your response. Let's continue exploring this concept.",
            "score": 0.6,
            "followUpQuestion": "",
            "dialogueComplete": True  # Complete on error to allow user to move on
        }


# sanitize_user_input has been moved to content_generators.py
# Import it if needed in this module for other functions
from .content_generators import sanitize_user_input


# Initialize Anthropic client
client = Anthropic(api_key=config.ANTHROPIC_API_KEY)


def call_anthropic_with_retry(system_prompt: str, user_message: str, max_retries: int = DEFAULT_MAX_RETRIES, timeout: int = DEFAULT_API_TIMEOUT_SECONDS) -> Any:
    """
    Call Anthropic API with retry logic and timeout.

    Args:
        system_prompt: System prompt text
        user_message: User message text
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds for each attempt (default: 30)

    Returns:
        Anthropic API response object

    Raises:
        Exception: If all retries fail
    """
    import time
    from anthropic import APIError, APIConnectionError, RateLimitError, APITimeoutError

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"API call attempt {attempt + 1}/{max_retries}")

            response = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=4096,
                timeout=timeout,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            logger.info(f"API call successful on attempt {attempt + 1}")
            return response

        except (APIConnectionError, APITimeoutError, RateLimitError) as e:
            # Transient errors - retry with exponential backoff
            last_error = e
            wait_time = RETRY_BACKOFF_BASE ** attempt  # 2^0=1s, 2^1=2s, 2^2=4s
            logger.warning(f"Transient API error on attempt {attempt + 1}: {type(e).__name__}: {str(e)}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")
                raise Exception(f"API call failed after {max_retries} attempts: {type(e).__name__}: {str(e)}")

        except APIError as e:
            # Non-transient API errors - don't retry
            logger.error(f"Non-transient API error: {type(e).__name__}: {str(e)}")
            raise Exception(f"API error: {type(e).__name__}: {str(e)}")

        except Exception as e:
            # Unexpected errors - don't retry
            logger.error(f"Unexpected error during API call: {type(e).__name__}: {str(e)}")
            raise Exception(f"Unexpected error: {type(e).__name__}: {str(e)}")

    # Should never reach here, but just in case
    raise Exception(f"API call failed: {last_error}")


# ============================================================================
# System Prompt Management
# ============================================================================

def load_system_prompt() -> str:
    """
    Load the tutor agent system prompt and confidence addendum.

    Returns:
        Complete system prompt as string
    """
    try:
        # Load main system prompt
        with open(config.SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            main_prompt = f.read()

        # Load confidence tracking addendum
        with open(config.CONFIDENCE_PROMPT_FILE, "r", encoding="utf-8") as f:
            confidence_addendum = f.read()

        # Combine prompts
        system_prompt = f"{main_prompt}\n\n{confidence_addendum}"

        logger.info("Loaded system prompt")
        return system_prompt

    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        raise


def load_content_generation_prompt(course_id: Optional[str] = None) -> str:
    """
    Load the content generation instructions.

    Args:
        course_id: Optional course ID to load course-specific prompt

    Returns:
        Content generation prompt as string
    """
    try:
        # Try to load course-specific prompt first
        if course_id:
            course_dir = config.get_course_dir(course_id)
            course_prompt_file = course_dir / "content-generation-addendum.md"
            if course_prompt_file.exists():
                with open(course_prompt_file, "r", encoding="utf-8") as f:
                    content_prompt = f.read()
                logger.info(f"Loaded course-specific content generation prompt for {course_id}")
                return content_prompt

        # Fall back to default prompt
        with open(config.CONTENT_GENERATION_PROMPT_FILE, "r", encoding="utf-8") as f:
            content_prompt = f.read()

        logger.info("Loaded default content generation prompt")
        return content_prompt

    except Exception as e:
        logger.error(f"Error loading content generation prompt: {e}")
        raise


def inject_learner_context(base_prompt: str, learner_id: str) -> str:
    """
    Inject learner-specific context into system prompt.

    Args:
        base_prompt: Base system prompt
        learner_id: Learner identifier

    Returns:
        System prompt with learner context
    """
    try:
        model = load_learner_model(learner_id)

        # Build learner context
        context = f"\n\n## Current Learner Context\n\n"
        context += f"**Learner ID**: {learner_id}\n"

        # Add learner name if available
        if model.get("learner_name"):
            context += f"**Learner Name**: {model['learner_name']}\n"

        # Add learner profile for personalization
        profile = model.get("profile", {})
        if profile:
            context += f"\n### Learner Profile (for Personalization)\n\n"

            if profile.get("background"):
                context += f"**Background & Motivation**: {profile['background']}\n"

            if profile.get("priorKnowledge"):
                pk = profile["priorKnowledge"]
                context += f"\n**Prior Knowledge**:\n"
                if pk.get("languageDetails"):
                    lang_text = pk['languageDetails'].lower()
                    context += f"- Languages studied: {pk['languageDetails']}\n"

                    # Auto-detect Romance languages
                    romance_languages = ['spanish', 'french', 'italian', 'portuguese', 'romanian', 'catalan']
                    has_romance = pk.get("hasRomanceLanguage") or any(lang in lang_text for lang in romance_languages)
                    if has_romance:
                        context += f"- Has studied Romance language - use cognates and comparisons!\n"

                    # Auto-detect inflected languages (with grammatical cases)
                    inflected_languages = ['german', 'russian', 'greek', 'ancient greek', 'polish', 'finnish', 'hungarian', 'czech', 'latin', 'sanskrit', 'icelandic']
                    has_inflected = pk.get("hasInflectedLanguage") or any(lang in lang_text for lang in inflected_languages)
                    if has_inflected:
                        context += f"- Has studied inflected language - familiar with cases!\n"
                elif pk.get("hasRomanceLanguage"):
                    context += f"- Has studied Romance language (Spanish/French) - use cognates and comparisons!\n"
                elif pk.get("hasInflectedLanguage"):
                    context += f"- Has studied inflected language (German) - familiar with cases!\n"

                if "understandsSubjectObject" in pk:
                    context += f"- Subject/Object understanding: {pk.get('understandsSubjectObject')}\n"
                    context += f"- Confidence level: {pk.get('subjectObjectConfidence', 'unknown')}\n"

            if profile.get("grammarExperience"):
                exp_map = {
                    "loved": "Enthusiastic about grammar - can use technical terminology",
                    "okay": "Has basic grammar foundation - balance terminology with explanation",
                    "confused": "Found grammar confusing - use simple language and clear examples",
                    "forgotten": "Needs grammar refresher - build from basics"
                }
                context += f"\n**Grammar Comfort**: {exp_map.get(profile['grammarExperience'], profile['grammarExperience'])}\n"

            if profile.get("learningStyle"):
                style_map = {
                    "narrative": "Prefers story-based learning through scenarios, conversations, and contextual examples",
                    "dialogue": "Prefers Socratic discussion - being asked questions and explaining their thinking",
                    "interactive": "Prefers hands-on exploration - clicking, dragging, and discovering patterns",
                    "varied": "Enjoys variety - mix different content types (tables, examples, exercises)"
                }
                context += f"**Learning Style**: {style_map.get(profile['learningStyle'], profile['learningStyle'])}\n"

                # Add specific teaching guidance based on learning style
                context += f"\n**Content Format Preference**: "
                if profile['learningStyle'] == "narrative":
                    context += "Generate 'example-set' content with rich contextual examples and stories. Include 'lesson' content with narrative explanations connecting grammar to real usage. Avoid videos.\n"
                elif profile['learningStyle'] == "dialogue":
                    context += "Generate 'dialogue' questions that ask the learner to explain their understanding. Use Socratic questioning. Let them articulate concepts in their own words. Avoid videos.\n"
                elif profile['learningStyle'] == "interactive":
                    context += "Generate interactive widgets: 'paradigm-table', 'declension-explorer', 'word-order-manipulator'. Let them click, explore, and discover patterns hands-on. Avoid videos.\n"
                elif profile['learningStyle'] == "varied":
                    context += "Vary the content types - alternate between paradigm tables, example sets with stories, dialogue questions, and fill-blank exercises. Keep it diverse. Avoid videos.\n"
                else:
                    context += "Use written text content with clear examples. Avoid videos.\n"

            if profile.get("interests"):
                context += f"**Interests**: {profile['interests']}\n"
                context += f"**Example Personalization**: Use examples related to {profile['interests'].split(',')[0].strip()} when possible.\n"

        context += f"\n### Learning Progress\n\n"
        context += f"**Current Concept**: {model['current_concept']}\n"
        context += f"**Concepts Completed**: {model['overall_progress']['concepts_completed']}\n"
        context += f"**Total Assessments**: {model['overall_progress']['total_assessments']}\n"

        # Add current concept progress if exists
        current_concept = model["current_concept"]
        if current_concept in model["concepts"]:
            concept_data = model["concepts"][current_concept]
            context += f"**Current Concept Status**: {concept_data['status']}\n"
            context += f"**Assessments for Current Concept**: {len(concept_data['assessments'])}\n"
            context += f"**Current Mastery Score**: {concept_data['mastery_score']:.2f}\n"

            # Add calibration metrics if available
            if concept_data["confidence_history"]:
                calibration_metrics = calculate_overall_calibration(concept_data["confidence_history"])
                context += f"**Calibration Accuracy**: {calibration_metrics['overall_accuracy']:.2f}\n"

        return base_prompt + context

    except Exception as e:
        logger.error(f"Error injecting learner context: {e}")
        # Return base prompt if context injection fails
        return base_prompt


# ============================================================================
# Tool Definitions for Claude API
# ============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "load_resource",
        "description": "Load a learning resource (text-explainer or examples) from the resource bank for a specific concept.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id": {
                    "type": "string",
                    "description": "The concept identifier (e.g., 'concept-001')"
                },
                "resource_type": {
                    "type": "string",
                    "enum": ["text-explainer", "examples"],
                    "description": "Type of resource to load"
                }
            },
            "required": ["concept_id", "resource_type"]
        }
    },
    {
        "name": "load_assessment",
        "description": "Load an assessment (dialogue, written, or applied) for a specific concept.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id": {
                    "type": "string",
                    "description": "The concept identifier (e.g., 'concept-001')"
                },
                "assessment_type": {
                    "type": "string",
                    "enum": ["dialogue", "written", "applied"],
                    "description": "Type of assessment to load"
                }
            },
            "required": ["concept_id", "assessment_type"]
        }
    },
    {
        "name": "load_concept_metadata",
        "description": "Load metadata for a concept including title, objectives, vocabulary, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id": {
                    "type": "string",
                    "description": "The concept identifier (e.g., 'concept-001')"
                }
            },
            "required": ["concept_id"]
        }
    },
    {
        "name": "track_confidence",
        "description": "Calculate calibration between student's self-reported confidence and actual performance. Returns calibration analysis and feedback.",
        "input_schema": {
            "type": "object",
            "properties": {
                "self_confidence": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Student's confidence rating (1-5)"
                },
                "actual_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Actual assessment score (0.0-1.0)"
                }
            },
            "required": ["self_confidence", "actual_score"]
        }
    },
    {
        "name": "update_learner_model",
        "description": "Update the learner's progress model with new assessment data. This records the assessment and updates mastery tracking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "learner_id": {
                    "type": "string",
                    "description": "The learner's unique identifier"
                },
                "concept_id": {
                    "type": "string",
                    "description": "The concept being assessed"
                },
                "assessment_data": {
                    "type": "object",
                    "description": "Assessment results including type, score, confidence, calibration",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["dialogue", "written", "applied"]
                        },
                        "score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "self_confidence": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5
                        },
                        "calibration": {
                            "type": "object"
                        },
                        "prompt_id": {
                            "type": "string"
                        }
                    },
                    "required": ["type", "score"]
                }
            },
            "required": ["learner_id", "concept_id", "assessment_data"]
        }
    },
    {
        "name": "calculate_mastery",
        "description": "Calculate the current mastery level for a concept and get recommendation (progress, continue, or support).",
        "input_schema": {
            "type": "object",
            "properties": {
                "learner_id": {
                    "type": "string",
                    "description": "The learner's unique identifier"
                },
                "concept_id": {
                    "type": "string",
                    "description": "The concept to check mastery for"
                }
            },
            "required": ["learner_id", "concept_id"]
        }
    },
    {
        "name": "get_next_concept",
        "description": "Get the next concept in the learning sequence after the current one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_concept_id": {
                    "type": "string",
                    "description": "The current concept identifier"
                }
            },
            "required": ["current_concept_id"]
        }
    },
    {
        "name": "load_external_source",
        "description": "Load full content from an external source (website, PDF, video transcript, etc.) that has been added to the course. Use this to reference external materials when creating content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                    "description": "The source identifier"
                },
                "concept_id": {
                    "type": "string",
                    "description": "Concept ID if this is a concept-specific source, omit for course-level sources"
                }
            },
            "required": ["source_id"]
        }
    },
    {
        "name": "generate_contextualized_example",
        "description": "Generate an example illustrating a concept, tailored to the learner's interests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id": {
                    "type": "string",
                    "description": "ID of the concept to illustrate"
                },
                "learner_interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of learner interests"
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easier", "appropriate", "harder"],
                    "description": "Difficulty level"
                }
            },
            "required": ["concept_id", "learner_interests"]
        }
    },
    {
        "name": "break_down_concept_application",
        "description": "Deconstructs a complex application of a concept into steps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id": {
                    "type": "string",
                    "description": "ID of the concept"
                },
                "student_work": {
                    "type": "string",
                    "description": "The student's attempt or question (optional)"
                },
                "problem_statement": {
                    "type": "string",
                    "description": "The problem being solved (optional)"
                }
            },
            "required": ["concept_id"]
        }
    },
    {
        "name": "compare_concepts",
        "description": "Creates a comparison matrix between two concepts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept_id_a": {
                    "type": "string",
                    "description": "First concept ID"
                },
                "concept_id_b": {
                    "type": "string",
                    "description": "Second concept ID"
                }
            },
            "required": ["concept_id_a", "concept_id_b"]
        }
    }
]


# ============================================================================
# Tool Execution Handler
# ============================================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any], learner_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a tool call and return the result.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        learner_id: Learner ID for course context (optional)

    Returns:
        Tool execution result
    """
    try:
        # Get course_id from learner model if available
        course_id = None
        if learner_id:
            try:
                learner_model = load_learner_model(learner_id)
                course_id = learner_model.get("current_course")
            except Exception as e:
                logger.warning(f"Could not load learner model for {learner_id}: {e}")

        if tool_name == "load_resource":
            result = load_resource(
                concept_id=tool_input["concept_id"],
                resource_type=tool_input["resource_type"],
                course_id=course_id
            )
            return {"success": True, "data": result}

        elif tool_name == "load_assessment":
            result = load_assessment(
                concept_id=tool_input["concept_id"],
                assessment_type=tool_input["assessment_type"],
                course_id=course_id
            )
            return {"success": True, "data": result}

        elif tool_name == "load_concept_metadata":
            result = load_concept_metadata(
                concept_id=tool_input["concept_id"],
                course_id=course_id
            )
            return {"success": True, "data": result}

        elif tool_name == "track_confidence":
            calibration = calculate_calibration(
                self_confidence=tool_input["self_confidence"],
                actual_score=tool_input["actual_score"]
            )
            feedback = get_calibration_feedback(calibration)
            return {
                "success": True,
                "data": {
                    "calibration": calibration,
                    "feedback": feedback
                }
            }

        elif tool_name == "update_learner_model":
            result = update_learner_model(
                learner_id=tool_input["learner_id"],
                concept_id=tool_input["concept_id"],
                assessment_data=tool_input["assessment_data"]
            )
            return {"success": True, "data": {"message": "Learner model updated successfully"}}

        elif tool_name == "calculate_mastery":
            result = calculate_mastery(
                learner_id=tool_input["learner_id"],
                concept_id=tool_input["concept_id"]
            )
            return {"success": True, "data": result}

        elif tool_name == "get_next_concept":
            result = get_next_concept(
                current_concept_id=tool_input["current_concept_id"],
                course_id=course_id
            )
            return {"success": True, "data": {"next_concept": result}}

        elif tool_name == "load_external_source":
            from .source_extraction import load_full_source_content
            from .config import config as app_config
            import json

            # Load metadata to find source URL and type
            source_id = tool_input["source_id"]
            concept_id = tool_input.get("concept_id")

            if concept_id:
                # Concept-level source
                concept_dir = app_config.get_concept_dir(concept_id, course_id)
                metadata_file = concept_dir / "metadata.json"
            else:
                # Course-level source
                course_dir = app_config.get_course_dir(course_id or app_config.DEFAULT_COURSE_ID)
                metadata_file = course_dir / "metadata.json"

            if not metadata_file.exists():
                return {"success": False, "error": "Metadata file not found"}

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Find source
            sources = metadata.get("sources", [])
            source = next((s for s in sources if s.get("id") == source_id), None)

            if not source:
                return {"success": False, "error": f"Source {source_id} not found"}

            # Load full content
            content_data = load_full_source_content(source["url"], source["type"])

            return {"success": True, "data": content_data}

        elif tool_name == "generate_contextualized_example":
            result = generate_contextualized_example(
                concept_id=tool_input["concept_id"],
                learner_interests=tool_input["learner_interests"],
                difficulty=tool_input.get("difficulty", "appropriate"),
                course_id=course_id
            )
            return {"success": True, "data": result}

        elif tool_name == "break_down_concept_application":
            result = break_down_concept_application(
                concept_id=tool_input["concept_id"],
                student_work=tool_input.get("student_work"),
                problem_statement=tool_input.get("problem_statement"),
                course_id=course_id
            )
            return {"success": True, "data": result}

        elif tool_name == "compare_concepts":
            result = compare_concepts(
                concept_id_a=tool_input["concept_id_a"],
                concept_id_b=tool_input["concept_id_b"],
                course_id=course_id
            )
            return {"success": True, "data": result}

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# Chat Function
# ============================================================================

def chat(
    learner_id: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Send a message to Claude and get a response, handling tool use.

    Args:
        learner_id: Unique identifier for the learner
        user_message: The user's message
        conversation_history: Previous conversation messages (optional)

    Returns:
        Dictionary containing response and updated conversation history
    """
    try:
        # Load system prompt with learner context
        base_prompt = load_system_prompt()
        system_prompt = inject_learner_context(base_prompt, learner_id)

        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = []

        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Make initial API call
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=conversation_history,
            tools=TOOL_DEFINITIONS
        )

        logger.info(f"Claude API call completed. Stop reason: {response.stop_reason}")

        # Handle tool use loop
        while response.stop_reason == "tool_use":
            # Add assistant's response to history
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # Process tool calls
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.info(f"Executing tool: {tool_name}")
                    logger.debug(f"Tool input: {tool_input}")

                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_input, learner_id)

                    # Add tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps(tool_result)
                    })

            # Add tool results to conversation
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continue conversation with tool results
            response = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=conversation_history,
                tools=TOOL_DEFINITIONS
            )

            logger.info(f"Claude API call (after tool use) completed. Stop reason: {response.stop_reason}")

        # Extract final text response
        assistant_message = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                assistant_message += content_block.text

        # Add final assistant response to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return {
            "success": True,
            "message": assistant_message,
            "conversation_history": conversation_history
        }

    except Exception as e:
        logger.error(f"Error in chat function: {e}")
        return {
            "success": False,
            "error": str(e),
            "conversation_history": conversation_history
        }


# ============================================================================
# Content Generation Function
# ============================================================================

def generate_content(learner_id: str, stage: str = "start", correctness: bool = None,
                     confidence: int = None, remediation_type: str = None,
                     question_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate personalized learning content based on learner profile and current stage.

    Args:
        learner_id: Unique identifier for the learner
        stage: Learning stage ("start", "practice", "assess", "remediate", "reinforce")
        correctness: Whether the previous answer was correct (for adaptive response)
        confidence: Confidence level 1-4 (for adaptive response)
        remediation_type: Type of remediation ("brief", "supportive", "full_calibration")
        question_context: Optional dict with question details for specific feedback:
            - scenario: The question scenario text
            - question: The question text
            - user_answer: Answer index or text the student selected
            - options: List of options (for multiple-choice)
            - correct_answer: The correct answer

    Returns:
        Dictionary containing generated content object
    """
    try:
        # Get question history to avoid repetition and load course info
        try:
            from .tools import load_learner_model
            learner_model = load_learner_model(learner_id)
            question_history = learner_model.get("question_history", [])
            concept_id = learner_model.get("current_concept", "concept-001")  # Get current concept for difficulty selection
            course_id = learner_model.get("current_course", config.DEFAULT_COURSE_ID)  # Get course for content loading
        except Exception:
            question_history = []
            concept_id = "concept-001"  # Default fallback
            course_id = config.DEFAULT_COURSE_ID

        # Load content generation prompt (course-specific if available)
        content_prompt = load_content_generation_prompt(course_id)

        # Load course metadata and inject into prompt
        try:
            import json
            course_dir = config.get_course_dir(course_id)
            course_metadata_path = course_dir / "metadata.json"

            if course_metadata_path.exists():
                with open(course_metadata_path, "r", encoding="utf-8") as f:
                    course_metadata = json.load(f)

                course_context = "\n\n## COURSE CONTEXT\n\n"
                course_context += f"**Course Title**: {course_metadata.get('title', 'Unknown Course')}\n"
                course_context += f"**Domain**: {course_metadata.get('domain', 'General')}\n"

                # Add taxonomy if present
                taxonomy = course_metadata.get('taxonomy', 'blooms')
                taxonomy_guidance = {
                    'blooms': "Use Bloom's Taxonomy levels (Remember, Understand, Apply, Analyze, Evaluate, Create) when crafting questions and content.",
                    'solo': "Use SOLO Taxonomy levels (Prestructural, Unistructural, Multistructural, Relational, Extended Abstract) when designing assessments.",
                    'fink': "Use Fink's Taxonomy of Significant Learning (Foundational Knowledge, Application, Integration, Human Dimension, Caring, Learning How to Learn)."
                }
                course_context += f"**Learning Taxonomy**: {taxonomy.title()} - {taxonomy_guidance.get(taxonomy, 'Apply appropriate cognitive levels in content design.')}\n"

                if course_metadata.get('course_learning_outcomes'):
                    course_context += f"**Course Learning Outcomes**:\n"
                    for clo in course_metadata['course_learning_outcomes']:
                        course_context += f"- {clo}\n"
                course_context += "\n**IMPORTANT**: All content, scenarios, and examples must be relevant to this course's subject matter and learning outcomes.\n"
            else:
                course_context = ""

            # Load current concept metadata
            concept_metadata_path = course_dir / concept_id / "metadata.json"
            if concept_metadata_path.exists():
                with open(concept_metadata_path, "r", encoding="utf-8") as f:
                    concept_metadata = json.load(f)

                course_context += f"\n### Current Concept: {concept_metadata.get('title', concept_id)}\n\n"

                # Add prerequisites if present
                if concept_metadata.get('prerequisites'):
                    prereqs = concept_metadata['prerequisites']
                    if prereqs:
                        course_context += f"**Prerequisites**: This concept builds on {', '.join(prereqs)}. Learners should already understand those concepts.\n"

                if concept_metadata.get('module_learning_outcomes'):
                    course_context += f"**Learning Outcomes for This Concept**:\n"
                    for mlo in concept_metadata['module_learning_outcomes']:
                        course_context += f"- {mlo}\n"
                course_context += "\n**CRITICAL**: Generate content ONLY about this specific concept and its learning outcomes. Use scenarios and examples from this domain.\n"
        except Exception as e:
            logger.warning(f"Could not load course metadata: {e}")
            course_context = ""

        # Load learner context and question history
        learner_context = inject_learner_context("", learner_id)

        # Combine prompts
        system_prompt = f"{content_prompt}\n\n{course_context}\n\n{learner_context}"

        # Add question history context if available
        if question_history:
            history_text = "\n\nRECENT QUESTIONS ASKED (do NOT repeat these):\n"
            for i, q in enumerate(question_history[-RECENT_QUESTIONS_DISPLAY_COUNT:], 1):
                history_text += f"{i}. {q.get('scenario', '')} {q.get('question', '')}\n"
            system_prompt += history_text

        # Check if cumulative review should be shown (only for practice stage)
        is_cumulative = False
        cumulative_concepts = []
        if stage in [STAGE_START, STAGE_PRACTICE]:
            try:
                is_cumulative = should_show_cumulative_review(learner_id)
                if is_cumulative:
                    cumulative_concepts = select_concepts_for_cumulative(learner_id, count=CUMULATIVE_REVIEW_CONCEPTS_COUNT)
                    logger.info(f"Generating cumulative review across concepts: {cumulative_concepts}")

                    # Load metadata for all selected concepts
                    concepts_metadata = []
                    for concept_id in cumulative_concepts:
                        metadata = load_concept_metadata(concept_id, course_id)
                        concepts_metadata.append({
                            "concept_id": concept_id,
                            "title": metadata.get("title", concept_id),
                            "description": metadata.get("description", "")
                        })

                    # Add cumulative context to system prompt
                    cumulative_context = "\n\n=== CUMULATIVE REVIEW MODE ===\n"
                    cumulative_context += "Generate a question that integrates concepts from MULTIPLE previously learned topics:\n"
                    for cm in concepts_metadata:
                        cumulative_context += f"- {cm['concept_id']}: {cm['title']} ({cm['description']})\n"
                    cumulative_context += "\nThe question should require the learner to apply knowledge from at least 2 of these concepts together.\n"
                    system_prompt += cumulative_context
            except ValueError as e:
                # Not enough concepts for cumulative review yet
                logger.info(f"Cumulative review not available: {e}")
                is_cumulative = False

        # Build generation request based on stage
        if stage == STAGE_PREVIEW:
            # PREVIEW MODE: Quick conceptual foundation before diagnostic
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'narrative')
            request = generate_preview_request(learning_style)

        elif stage == STAGE_START:
            # DIAGNOSTIC-FIRST: Always start with a question
            # Use adaptive difficulty based on recent performance
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'varied')
            difficulty = select_question_difficulty(learner_id, concept_id)
            logger.info(f"Selected difficulty for START stage: {difficulty}, learning style: {learning_style}")
            request = generate_diagnostic_request(is_cumulative, cumulative_concepts, difficulty, learning_style)

        elif stage == STAGE_PRACTICE:
            # Generate next diagnostic question
            # Use adaptive difficulty based on recent performance
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'varied')
            difficulty = select_question_difficulty(learner_id, concept_id)
            logger.info(f"Selected difficulty for PRACTICE stage: {difficulty}, learning style: {learning_style}")
            request = generate_practice_request(is_cumulative, cumulative_concepts, difficulty, learning_style)

        elif stage == STAGE_ASSESS:
            # Dialogue questions disabled - generate multiple-choice instead
            # (This stage should not be used, but keeping as fallback to multiple-choice)
            request = generate_diagnostic_request(is_cumulative=False)

        elif stage == STAGE_REMEDIATE:
            # Generate remediation content after incorrect answer
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'narrative')
            request = generate_remediation_request(
                question_context,
                confidence,
                remediation_type,
                learning_style
            )

        elif stage == STAGE_REINFORCE:
            # Generate reinforcement content after correct but uncertain answer
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'narrative')
            request = generate_reinforcement_request(
                question_context,
                confidence,
                learning_style
            )

        else:
            request = "Generate a 'multiple-choice' diagnostic question with scenario. Respond ONLY with the JSON object, no other text."

        # Handle pre-authored teaching moments (not AI-generated)
        if request == "USE_TEACHING_MOMENT":
            from .tools import select_personalized_teaching_moment
            try:
                teaching_moment = select_personalized_teaching_moment(
                    concept_id=concept_id,
                    learner_id=learner_id,
                    course_id=course_id
                )
                logger.info(f"Serving pre-authored teaching moment: {teaching_moment.get('teaching_moment_id')}")
                return {
                    "success": True,
                    "content": teaching_moment,
                    "source": "pre-authored"
                }
            except FileNotFoundError as e:
                # No teaching moments for this concept, fall back to another interactive widget
                logger.warning(f"No teaching moments available for {concept_id}, falling back to declension-explorer")
                request = (
                    "Generate a 'declension-explorer' interactive widget that lets the learner "
                    "explore noun or verb forms. Include a base word and show how it changes across "
                    "different cases/forms. Provide interactive elements where the learner can see patterns. "
                    "Include a brief task asking them to predict or identify a specific form. "
                    "Respond ONLY with the JSON object, no other text."
                )
            except Exception as e:
                logger.error(f"Error loading teaching moment: {e}")
                request = (
                    "Generate a 'declension-explorer' interactive widget that lets the learner "
                    "explore noun or verb forms. Include a base word and show how it changes across "
                    "different cases/forms. Respond ONLY with the JSON object, no other text."
                )

        # Make API call with retry logic
        response = call_anthropic_with_retry(
            system_prompt=system_prompt,
            user_message=request,
            max_retries=3,
            timeout=30
        )

        logger.info(f"Content generation API call completed. Stop reason: {response.stop_reason}")

        # Extract text response
        content_text = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                content_text += content_block.text

        # Strip markdown code fences if present
        content_text = content_text.strip()
        logger.info(f"Raw content text starts with: {content_text[:50]}")

        if content_text.startswith("```"):
            logger.info("Stripping markdown code fences from response")
            # Remove opening fence (```json or ```)
            lines = content_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content_text = '\n'.join(lines).strip()
            logger.info(f"After stripping, content starts with: {content_text[:50]}")

        # Parse JSON
        try:
            content_obj = json.loads(content_text)
            content_type = content_obj.get('type', 'unknown')

            # CRITICAL: Ensure content always has a type field
            if 'type' not in content_obj or not content_obj['type']:
                logger.warning(f"Content missing type field, inferring from structure...")
                # Try to infer type from content structure
                if 'sections' in content_obj:
                    content_obj['type'] = 'lesson'
                elif 'forms' in content_obj and 'noun' in content_obj:
                    content_obj['type'] = 'paradigm-table'
                elif 'examples' in content_obj:
                    content_obj['type'] = 'example-set'
                elif 'options' in content_obj and 'correctAnswer' in content_obj:
                    content_obj['type'] = 'multiple-choice'
                elif 'blanks' in content_obj:
                    content_obj['type'] = 'fill-blank'
                elif 'scenario' in content_obj and 'part1' in content_obj:
                    content_obj['type'] = 'teaching-moment'
                elif 'question' in content_obj and 'options' not in content_obj:
                    # Dialogue: has question but no options (open-ended)
                    content_obj['type'] = 'dialogue'
                else:
                    content_obj['type'] = 'lesson'  # Default fallback
                content_type = content_obj['type']
                logger.info(f"Inferred content type: {content_type}")

            logger.info(f"Successfully generated content type: {content_type}")

            # Validate diagnostic question content
            is_valid, error_msg = validate_diagnostic_content(content_obj)
            if not is_valid:
                logger.error(f"Content validation failed: {error_msg}")
                logger.error(f"Invalid content: {json.dumps(content_obj, indent=2)}")
                return {
                    "success": False,
                    "error": f"Content validation failed: {error_msg}",
                    "raw_response": content_text
                }

            # Attach external resources for lesson/example-set content
            if content_type in ['lesson', 'example-set'] and stage in ['remediate', 'reinforce']:
                from .tools import load_external_resources, load_learner_model
                try:
                    learner_model = load_learner_model(learner_id)
                    current_concept = learner_model.get('current_concept', 'concept-001')
                    learner_profile = learner_model.get('profile', {})

                    # Load external resources for this concept
                    external_resources = load_external_resources(current_concept, learner_profile)

                    if external_resources:
                        # Add top resources to the content
                        content_obj['external_resources'] = external_resources[:MAX_EXTERNAL_RESOURCES_TO_ATTACH]
                        logger.info(f"Attached {len(content_obj['external_resources'])} external resources")
                except Exception as e:
                    logger.warning(f"Failed to attach external resources: {e}")

            # Add cumulative review metadata if applicable
            if is_cumulative:
                content_obj['is_cumulative'] = True
                content_obj['cumulative_concepts'] = cumulative_concepts
                logger.info(f"Marked content as cumulative review across: {cumulative_concepts}")

            # Determine if confidence rating should be shown for this question (adaptive frequency)
            show_confidence = False
            if content_type in ['multiple-choice', 'fill-blank', 'dialogue']:  # Only for question types
                from .tools import should_show_confidence_rating, load_learner_model
                try:
                    learner_model = load_learner_model(learner_id)
                    current_concept = learner_model.get('current_concept', 'concept-001')
                    show_confidence = should_show_confidence_rating(learner_id, current_concept)
                    logger.info(f"Confidence rating for this question: {show_confidence}")
                except Exception as e:
                    logger.warning(f"Failed to determine confidence rating: {e}, defaulting to True")
                    show_confidence = True

            content_obj['show_confidence'] = show_confidence

            # Strip any video content before returning (hard enforcement)
            content_obj = strip_video_content(content_obj)

            return {
                "success": True,
                "content": content_obj
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {content_text}")
            # Return error content
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "raw_response": content_text
            }

    except Exception as e:
        import traceback
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stage": stage,
            "learner_id": learner_id,
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error generating content: {error_details['error_type']}: {error_details['error_message']}")
        logger.error(f"Full traceback:\n{error_details['traceback']}")
        return {
            "success": False,
            "error": f"{error_details['error_type']}: {error_details['error_message']}",
            "error_details": error_details
        }
