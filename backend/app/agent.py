"""
Claude API Integration with Tool Use

This module handles interaction with Claude API, including tool definitions,
system prompt management, and conversation handling.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from anthropic import Anthropic
from .config import config
from .tools import (
    load_resource,
    load_assessment,
    load_concept_metadata,
    update_learner_model,
    calculate_mastery,
    get_next_concept,
    load_learner_model,
    should_show_cumulative_review,
    select_concepts_for_cumulative
)
from .confidence import (
    calculate_calibration,
    get_calibration_feedback,
    should_intervene_on_confidence,
    get_calibration_pattern_feedback,
    calculate_overall_calibration
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


# Initialize Anthropic client
client = Anthropic(api_key=config.ANTHROPIC_API_KEY)


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


def load_content_generation_prompt() -> str:
    """
    Load the content generation instructions.

    Returns:
        Content generation prompt as string
    """
    try:
        with open(config.CONTENT_GENERATION_PROMPT_FILE, "r", encoding="utf-8") as f:
            content_prompt = f.read()

        logger.info("Loaded content generation prompt")
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
                    context += f"- Languages studied: {pk['languageDetails']}\n"
                if pk.get("hasRomanceLanguage"):
                    context += f"- Has studied Romance language (Spanish/French) - use cognates and comparisons!\n"
                if pk.get("hasInflectedLanguage"):
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
                    "visual": "Prefers video explanations and visual structured displays (tables, charts)",
                    "connections": "Prefers written articles, guides, and connecting to English/other languages",
                    "practice": "Prefers interactive practice exercises, drills, and hands-on activities"
                }
                context += f"**Learning Style**: {style_map.get(profile['learningStyle'], profile['learningStyle'])}\n"

                # Add specific teaching guidance based on learning style
                context += f"\n**Content Format Preference**: "
                if profile['learningStyle'] == "visual":
                    context += "For remediation/reinforcement, generate 'paradigm-table' content showing structured grammar tables. Use visual organization.\n"
                elif profile['learningStyle'] == "connections":
                    context += "For remediation/reinforcement, generate 'lesson' or 'example-set' content with written explanations and connections to English.\n"
                elif profile['learningStyle'] == "practice":
                    context += "For remediation/reinforcement, generate 'fill-blank' exercises for hands-on practice. Include hints.\n"

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
    }
]


# ============================================================================
# Tool Execution Handler
# ============================================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call and return the result.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool

    Returns:
        Tool execution result
    """
    try:
        if tool_name == "load_resource":
            result = load_resource(
                concept_id=tool_input["concept_id"],
                resource_type=tool_input["resource_type"]
            )
            return {"success": True, "data": result}

        elif tool_name == "load_assessment":
            result = load_assessment(
                concept_id=tool_input["concept_id"],
                assessment_type=tool_input["assessment_type"]
            )
            return {"success": True, "data": result}

        elif tool_name == "load_concept_metadata":
            result = load_concept_metadata(
                concept_id=tool_input["concept_id"]
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
                current_concept_id=tool_input["current_concept_id"]
            )
            return {"success": True, "data": {"next_concept": result}}

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
                    tool_result = execute_tool(tool_name, tool_input)

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
        # Load content generation prompt
        content_prompt = load_content_generation_prompt()

        # Load learner context and question history
        learner_context = inject_learner_context("", learner_id)

        # Get question history to avoid repetition
        try:
            from .tools import load_learner_model
            learner_model = load_learner_model(learner_id)
            question_history = learner_model.get("question_history", [])
        except Exception:
            question_history = []

        # Combine prompts
        system_prompt = f"{content_prompt}\n\n{learner_context}"

        # Add question history context if available
        if question_history:
            history_text = "\n\nRECENT QUESTIONS ASKED (do NOT repeat these):\n"
            for i, q in enumerate(question_history[-5:], 1):  # Show last 5 questions
                history_text += f"{i}. {q.get('scenario', '')} {q.get('question', '')}\n"
            system_prompt += history_text

        # Check if cumulative review should be shown (only for practice stage)
        is_cumulative = False
        cumulative_concepts = []
        if stage in ["start", "practice"]:
            try:
                is_cumulative = should_show_cumulative_review(learner_id)
                if is_cumulative:
                    cumulative_concepts = select_concepts_for_cumulative(learner_id, count=3)
                    logger.info(f"Generating cumulative review across concepts: {cumulative_concepts}")

                    # Load metadata for all selected concepts
                    concepts_metadata = []
                    for concept_id in cumulative_concepts:
                        metadata = load_concept_metadata(concept_id)
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
        if stage == "preview":
            # PREVIEW MODE: Quick conceptual foundation before diagnostic (addresses audit feedback)
            # Adapt preview format to learning style
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'connections')

            if learning_style == 'visual':
                request = "Generate a brief 'paradigm-table' preview (30-second scan) showing the key grammatical patterns for this concept. Include a very short explanation (2-3 sentences max). This is a quick preview before assessment. Respond ONLY with the JSON object, no other text."
            elif learning_style == 'practice':
                request = "Generate a single 'fill-blank' exercise preview with generous hints showing the key pattern for this concept. This is a quick guided practice before assessment. Respond ONLY with the JSON object, no other text."
            else:  # connections
                request = "Generate a brief 'lesson' preview (30-second read) explaining the core concept and how it connects to familiar ideas (English grammar, etc.). Keep it short - this is just a conceptual foundation before assessment. Respond ONLY with the JSON object, no other text."

        elif stage == "start":
            # DIAGNOSTIC-FIRST: Always start with a question
            if is_cumulative:
                request = f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates the concepts listed above. The scenario should naturally require applying knowledge from at least 2 of those concepts. Include a rich Roman context. Mark this as is_cumulative: true in the metadata. Respond ONLY with the JSON object, no other text."
            else:
                request = "Generate a 'multiple-choice' diagnostic question with a NEW scenario (different from any shown above). This is the first question for the current concept. Include a rich Roman context (inscription, letter, etc.). Respond ONLY with the JSON object, no other text."

        elif stage == "practice":
            # Generate next diagnostic question
            if is_cumulative:
                request = f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates concepts from the list above. Create a scenario that requires applying knowledge from at least 2 of those concepts together. Use a different Roman setting. Mark this as is_cumulative: true in the metadata. Respond ONLY with the JSON object, no other text."
            else:
                request = "Generate a 'multiple-choice' diagnostic question with a COMPLETELY DIFFERENT scenario from those listed above. Vary the context: use different Latin words, different Roman settings (forum, bath, temple, road sign, etc.), different grammatical cases. Increase difficulty slightly. Respond ONLY with the JSON object, no other text."

        elif stage == "assess":
            # Deep understanding check
            request = "Generate a 'dialogue' type question requiring explanation, not just recall. Respond ONLY with the JSON object, no other text."

        elif stage == "remediate":
            # Get context about what they just answered wrong
            last_question_context = ""

            # Prioritize question_context parameter (passed directly from current question)
            if question_context:
                # Build detailed context with the actual question and answer choices
                scenario = question_context.get('scenario', '')
                question = question_context.get('question', '')
                user_ans_idx = question_context.get('user_answer', 'unknown')
                correct_ans_idx = question_context.get('correct_answer', 'unknown')
                options = question_context.get('options', [])

                # Get the actual text of what they chose vs correct answer
                user_answer_text = options[user_ans_idx] if isinstance(user_ans_idx, int) and options and user_ans_idx < len(options) else str(user_ans_idx)
                correct_answer_text = options[correct_ans_idx] if isinstance(correct_ans_idx, int) and options and correct_ans_idx < len(options) else str(correct_ans_idx)

                last_question_context = f"\n\n=== THE QUESTION THEY JUST ANSWERED INCORRECTLY ===\n\nScenario: {scenario}\n\nQuestion: {question}\n\nTHEY CHOSE: '{user_answer_text}' (Option {user_ans_idx})\n\nCORRECT ANSWER: '{correct_answer_text}' (Option {correct_ans_idx})\n\nAll Options:\n"
                for i, opt in enumerate(options):
                    marker = "✓ CORRECT" if i == correct_ans_idx else ("✗ THEY CHOSE THIS" if i == user_ans_idx else "")
                    last_question_context += f"{i}. {opt} {marker}\n"
                last_question_context += "\n"

            # Fallback to question history if no direct context provided
            elif question_history and len(question_history) > 0:
                last_q = question_history[-1]
                user_ans = last_q.get('user_answer', 'unknown')
                correct_ans = last_q.get('correct_answer', 'unknown')
                last_question_context = f"\n\nTHE QUESTION THEY JUST ANSWERED INCORRECTLY:\nScenario: {last_q.get('scenario', '')}\nQuestion: {last_q.get('question', '')}\nThey chose: {user_ans}\nCorrect answer: {correct_ans}\n"

            # Determine preferred content format based on learner style
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'connections')

            # Map learning style to content type
            preferred_content_type = 'lesson'  # default
            if learning_style == 'visual':
                preferred_content_type = 'paradigm-table'
            elif learning_style == 'practice':
                preferred_content_type = 'fill-blank'
            elif learning_style == 'connections':
                preferred_content_type = 'lesson'

            # Adaptive remediation based on confidence
            if remediation_type == "full_calibration":
                if preferred_content_type == 'paradigm-table':
                    request = f"The student answered incorrectly with {confidence}/4 confidence (overconfident).{last_question_context}Generate a 'paradigm-table' that: 1) Shows the complete declension table for the grammar concept they missed, 2) Highlights the specific form they should have chosen (in the correct_answer field), 3) Includes explanation text that STARTS with: 'You chose [their answer], but looking at the complete paradigm, the correct answer is [correct answer] because...' 4) Uses their interests in the explanation. Respond ONLY with the JSON object, no other text."
                elif preferred_content_type == 'fill-blank':
                    request = f"The student answered incorrectly with {confidence}/4 confidence (overconfident).{last_question_context}Generate a 'fill-blank' exercise that: 1) Targets the SPECIFIC grammar concept they misunderstood, 2) Uses their interests in the sentence, 3) Includes helpful hints that address their misconception, 4) Has exactly 1 blank focusing on the concept they got wrong. Respond ONLY with the JSON object, no other text."
                else:
                    request = f"The student answered incorrectly with {confidence}/4 confidence (overconfident).{last_question_context}Generate a 'lesson' that: 1) STARTS with: 'You chose [their answer], which suggests [what misconception this reveals]. However, the correct answer is [correct answer] because...' 2) Explains the SPECIFIC grammatical concept they misunderstood, 3) Provides 2-3 examples using their interests (see Learner Profile above - ACTUALLY use those topics in your examples, not generic ones!), 4) Includes calibration feedback about recognizing when to be less certain. CRITICAL: The examples MUST relate to the specific interests mentioned in the Learner Profile. Respond ONLY with the JSON object, no other text."
            elif remediation_type == "supportive":
                if preferred_content_type == 'paradigm-table':
                    request = f"The student answered incorrectly with {confidence}/4 confidence (aware of uncertainty).{last_question_context}Generate a supportive 'paradigm-table' with: 1) Complete declension table, 2) Encouraging explanation that validates their awareness of difficulty, 3) Clear marking of the correct answer. Be gentle. Respond ONLY with the JSON object, no other text."
                elif preferred_content_type == 'fill-blank':
                    request = f"The student answered incorrectly with {confidence}/4 confidence (aware of uncertainty).{last_question_context}Generate an encouraging 'fill-blank' exercise with: 1) Sentence using their interests, 2) Generous hints to build confidence, 3) Focus on the concept they missed. Be supportive. Respond ONLY with the JSON object, no other text."
                else:
                    request = f"The student answered incorrectly with {confidence}/4 confidence (low confidence, aware of uncertainty).{last_question_context}Generate a supportive 'lesson' or 'example-set' that: 1) Explains: 'You chose [their answer], but the correct answer is [correct answer] because...' 2) Directly addresses why their specific choice was wrong, 3) Provides 2-3 encouraging examples using their interests from the Learner Profile (ACTUALLY use those topics!). Be gentle and encouraging. Respond ONLY with the JSON object, no other text."
            else:
                if preferred_content_type == 'paradigm-table':
                    request = f"Generate a 'paradigm-table' showing the grammar concept from the most recent question.{last_question_context}Include brief explanation. Respond ONLY with the JSON object, no other text."
                elif preferred_content_type == 'fill-blank':
                    request = f"Generate a 'fill-blank' exercise to practice the concept from the most recent question.{last_question_context}Use their interests. Include hints. Respond ONLY with the JSON object, no other text."
                else:
                    request = f"Generate a brief 'lesson' to clarify the concept tested in the most recent question.{last_question_context}Start by explaining: 'You chose [their answer], but the correct answer is [correct answer].' Then briefly explain the specific concept and provide 1-2 examples using their interests (see Learner Profile). Respond ONLY with the JSON object, no other text."

        elif stage == "reinforce":
            # Get context about what they answered correctly but uncertainly
            last_question_context = ""

            # Prioritize question_context parameter (passed directly from current question)
            if question_context:
                scenario = question_context.get('scenario', '')
                question = question_context.get('question', '')
                user_ans_idx = question_context.get('user_answer', 'unknown')
                correct_ans_idx = question_context.get('correct_answer', 'unknown')
                options = question_context.get('options', [])

                # Get the actual text of the correct answer they chose
                correct_answer_text = options[correct_ans_idx] if isinstance(correct_ans_idx, int) and options and correct_ans_idx < len(options) else str(correct_ans_idx)

                last_question_context = f"\n\n=== THE QUESTION THEY JUST ANSWERED CORRECTLY (but with low confidence) ===\n\nScenario: {scenario}\n\nQuestion: {question}\n\nTHEIR ANSWER: '{correct_answer_text}' (Option {correct_ans_idx}) ✓ CORRECT\n\n"

            # Fallback to question history
            elif question_history and len(question_history) > 0:
                last_q = question_history[-1]
                last_question_context = f"\n\nTHE QUESTION THEY JUST ANSWERED CORRECTLY (but with low confidence):\nScenario: {last_q.get('scenario', '')}\nQuestion: {last_q.get('question', '')}\n"

            # Determine preferred content format based on learner style
            learner_model = load_learner_model(learner_id)
            learning_style = learner_model.get('profile', {}).get('learningStyle', 'connections')

            # Brief reinforcement for correct but uncertain answers - adapt format to preference
            if learning_style == 'visual':
                request = f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident).{last_question_context}Generate a brief 'paradigm-table' showing the pattern they correctly identified. Include encouraging explanation. Keep it short - they already know this! Respond ONLY with the JSON object, no other text."
            elif learning_style == 'practice':
                request = f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident).{last_question_context}Generate a quick 'fill-blank' exercise to reinforce what they got right. Include positive hints. Keep it short - they already know this! Respond ONLY with the JSON object, no other text."
            else:
                request = f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident).{last_question_context}Generate a brief 'example-set' that validates their answer to THAT specific question and builds confidence. Keep it short - they already know this! Respond ONLY with the JSON object, no other text."

        else:
            request = "Generate a 'multiple-choice' diagnostic question with scenario. Respond ONLY with the JSON object, no other text."

        # Make API call
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": request
            }]
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
                        # Add top 2 resources to the content
                        content_obj['external_resources'] = external_resources[:2]
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
        logger.error(f"Error generating content: {e}")
        return {
            "success": False,
            "error": str(e)
        }
