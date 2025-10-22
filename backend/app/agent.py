"""
Claude API Integration with Tool Use

This module handles interaction with Claude API, including tool definitions,
system prompt management, and conversation handling.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from .config import config
from .tools import (
    load_resource,
    load_assessment,
    load_concept_metadata,
    update_learner_model,
    calculate_mastery,
    get_next_concept,
    load_learner_model
)
from .confidence import (
    calculate_calibration,
    get_calibration_feedback,
    should_intervene_on_confidence,
    get_calibration_pattern_feedback,
    calculate_overall_calibration
)

logger = logging.getLogger(__name__)

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
                    "connections": "Prefers connections to English words and cognates",
                    "stories": "Learns best through context and example sentences",
                    "patterns": "Likes to see patterns and systematic logic",
                    "repetition": "Benefits from practice and repetition"
                }
                context += f"**Learning Style**: {style_map.get(profile['learningStyle'], profile['learningStyle'])}\n"

                # Add specific teaching guidance based on learning style
                context += f"\n**Teaching Strategy**: "
                if profile['learningStyle'] == "connections":
                    context += "Show English derivatives and cognates with other languages they know.\n"
                elif profile['learningStyle'] == "stories":
                    context += "Use example sentences and contextual learning.\n"
                elif profile['learningStyle'] == "patterns":
                    context += "Highlight patterns, endings, and systematic rules.\n"
                elif profile['learningStyle'] == "repetition":
                    context += "Provide practice exercises and review.\n"

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
                     confidence: int = None, remediation_type: str = None) -> Dict[str, Any]:
    """
    Generate personalized learning content based on learner profile and current stage.

    Args:
        learner_id: Unique identifier for the learner
        stage: Learning stage ("start", "practice", "assess", "remediate", "reinforce")
        correctness: Whether the previous answer was correct (for adaptive response)
        confidence: Confidence level 1-4 (for adaptive response)
        remediation_type: Type of remediation ("brief", "supportive", "full_calibration")

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

        # Build generation request based on stage
        if stage == "start":
            # DIAGNOSTIC-FIRST: Always start with a question
            request = "Generate a 'multiple-choice' diagnostic question with a NEW scenario (different from any shown above). This is the first question for the current concept. Include a rich Roman context (inscription, letter, etc.). Respond ONLY with the JSON object, no other text."

        elif stage == "practice":
            # Generate next diagnostic question
            request = "Generate a 'multiple-choice' diagnostic question with a COMPLETELY DIFFERENT scenario from those listed above. Vary the context: use different Latin words, different Roman settings (forum, bath, temple, road sign, etc.), different grammatical cases. Increase difficulty slightly. Respond ONLY with the JSON object, no other text."

        elif stage == "assess":
            # Deep understanding check
            request = "Generate a 'dialogue' type question requiring explanation, not just recall. Respond ONLY with the JSON object, no other text."

        elif stage == "remediate":
            # Get context about what they just answered wrong
            last_question_context = ""
            if question_history and len(question_history) > 0:
                last_q = question_history[-1]
                user_ans = last_q.get('user_answer', 'unknown')
                correct_ans = last_q.get('correct_answer', 'unknown')
                last_question_context = f"\n\nTHE QUESTION THEY JUST ANSWERED INCORRECTLY:\nScenario: {last_q.get('scenario', '')}\nQuestion: {last_q.get('question', '')}\nThey chose: {user_ans}\nCorrect answer: {correct_ans}\n"

            # Adaptive remediation based on confidence
            if remediation_type == "full_calibration":
                request = f"The student answered incorrectly with {confidence}/4 confidence (overconfident).{last_question_context}Generate a 'lesson' that: 1) Directly addresses the SPECIFIC concept tested in the question above, 2) Explains WHY their chosen answer was wrong and what misconception it reveals, 3) Includes calibration feedback about recognizing when to be less certain. Focus on the exact misconception revealed by their wrong answer. Respond ONLY with the JSON object, no other text."
            elif remediation_type == "supportive":
                request = f"The student answered incorrectly with {confidence}/4 confidence (low confidence, aware of uncertainty).{last_question_context}Generate a supportive 'lesson' or 'example-set' that directly addresses the SPECIFIC concept from the question above. Explain why their chosen answer was incorrect, but be gentle and encouraging. Respond ONLY with the JSON object, no other text."
            else:
                request = f"Generate a brief 'lesson' to clarify the concept tested in the most recent question.{last_question_context}Explain why their answer was incorrect. Respond ONLY with the JSON object, no other text."

        elif stage == "reinforce":
            # Get context about what they answered correctly but uncertainly
            last_question_context = ""
            if question_history and len(question_history) > 0:
                last_q = question_history[-1]
                last_question_context = f"\n\nTHE QUESTION THEY JUST ANSWERED CORRECTLY (but with low confidence):\nScenario: {last_q.get('scenario', '')}\nQuestion: {last_q.get('question', '')}\n"

            # Brief reinforcement for correct but uncertain answers
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
