"""
Tutor Agent: AI-powered "Talk to Tutor" conversations

Handles conversational interactions between learner and Latin tutor.
Implements guardrails, context injection, and Socratic teaching style.
"""

import anthropic
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .config import config
from .conversations import Conversation, Message, build_conversation_context
from .tools import load_concept_metadata

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


# ============================================================================
# System Prompt Loading
# ============================================================================

def load_tutor_system_prompt() -> str:
    """Load the tutor system prompt template."""
    try:
        prompt_file = config.PROMPTS_DIR / "tutor-system-prompt.md"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Tutor system prompt not found at {prompt_file}")

        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        logger.error(f"Error loading tutor system prompt: {e}")
        raise


# ============================================================================
# Context Formatting
# ============================================================================

def format_tutor_system_prompt(context: Dict[str, Any]) -> str:
    """
    Format the tutor system prompt with learner-specific context.

    Args:
        context: Dictionary containing learner profile, recent questions, struggles, etc.

    Returns:
        Formatted system prompt string
    """
    try:
        # Load base prompt template
        template = load_tutor_system_prompt()

        # Extract learner profile
        profile = context.get("learner_profile", {})
        learning_style = profile.get("learningStyle", "unknown")

        # Learning style descriptions
        learning_style_descriptions = {
            "narrative": "prefers story-based learning through scenarios, conversations, and contextual examples",
            "varied": "enjoys variety - mix of tables, examples, exercises, and different content types",
            "dialogue": "prefers interactive back-and-forth conversation and guided discovery"
        }

        # Get concept metadata
        concept_id = context.get("current_concept", "concept-001")
        try:
            metadata = load_concept_metadata(concept_id)
            concept_title = metadata.get("title", concept_id)
        except:
            concept_title = concept_id

        # Format struggling topics
        struggling_topics_list = context.get("struggling_topics", [])
        if struggling_topics_list:
            struggling_topics = "The student has been struggling with:\n" + "\n".join(
                f"- {topic}" for topic in struggling_topics_list
            )
        else:
            struggling_topics = "No significant struggles detected yet."

        # Format recent questions
        recent_questions_list = context.get("recent_questions", [])
        if recent_questions_list:
            recent_questions = "Recent assessment questions:\n" + "\n".join(
                f"- Q: {q.get('question_text', 'N/A')} | Answer: {q.get('user_answer', 'N/A')} | Correct: {q.get('was_correct', False)}"
                for q in recent_questions_list[-3:]  # Last 3 questions
            )
        else:
            recent_questions = "No recent questions yet."

        # Fill in template placeholders
        formatted_prompt = template.format(
            learner_name=context.get("learner_name", "Student"),
            concept_id=concept_id,
            concept_title=concept_title,
            learning_style=learning_style,
            learning_style_description=learning_style_descriptions.get(learning_style, "unknown preference"),
            interests=profile.get("interests", "various topics"),
            calibration_status=context.get("calibration_status", "unknown"),
            struggling_topics=struggling_topics,
            recent_questions=recent_questions
        )

        return formatted_prompt

    except Exception as e:
        logger.error(f"Error formatting tutor system prompt: {e}")
        raise


# ============================================================================
# Conversation Generation
# ============================================================================

def generate_tutor_response(
    conversation: Conversation,
    user_message: str,
    temperature: float = 0.7
) -> str:
    """
    Generate a tutor response using Claude API.

    Args:
        conversation: The conversation object with history
        user_message: The new message from the student
        temperature: Sampling temperature (0.7 for conversational responses)

    Returns:
        The tutor's response string
    """
    try:
        # Build system prompt with context
        system_prompt = format_tutor_system_prompt(conversation.context)

        # Build message history for Claude API
        messages = []

        # Add conversation history (exclude system messages)
        for msg in conversation.messages:
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add new user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        logger.info(f"Generating tutor response for conversation {conversation.conversation_id}")

        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=temperature,
            system=system_prompt,
            messages=messages
        )

        # Extract response text
        response_text = response.content[0].text

        logger.info(f"Generated tutor response ({len(response_text)} chars)")
        return response_text

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please try again in a moment."

    except Exception as e:
        logger.error(f"Error generating tutor response: {e}")
        return "I encountered an error. Please try asking your question again."


# ============================================================================
# Conversation Management
# ============================================================================

def start_tutor_conversation(learner_id: str, concept_id: str) -> Conversation:
    """
    Start a new tutor conversation.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being studied

    Returns:
        New Conversation object
    """
    try:
        from .conversations import Conversation, generate_conversation_id

        # Generate conversation ID
        conversation_id = generate_conversation_id(learner_id, "tutor")

        # Build context
        context = build_conversation_context(learner_id, concept_id)

        # Create conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            learner_id=learner_id,
            conversation_type="tutor",
            concept_id=concept_id,
            context=context,
            counts_toward_progress=True
        )

        # Add initial greeting from tutor
        greeting = generate_tutor_greeting(context)
        conversation.add_message("assistant", greeting)

        logger.info(f"Started tutor conversation {conversation_id}")
        return conversation

    except Exception as e:
        logger.error(f"Error starting tutor conversation: {e}")
        raise


def generate_tutor_greeting(context: Dict[str, Any]) -> str:
    """Generate a personalized greeting from the tutor."""
    learner_name = context.get("learner_name", "there")
    concept_id = context.get("current_concept", "concept-001")

    try:
        metadata = load_concept_metadata(concept_id)
        concept_title = metadata.get("title", "Latin grammar")
    except:
        concept_title = "Latin grammar"

    greeting = f"Hi {learner_name}! I'm here to help you with {concept_title}. "

    # Add personalized touch based on calibration status
    calibration = context.get("calibration_status", "unknown")
    if calibration == "overconfident":
        greeting += "I see you've been working through some tricky questions. Let's talk through any concepts that are confusing. What would you like to clarify?"
    elif calibration == "underconfident":
        greeting += "You're doing better than you think! What questions do you have? I'm here to help you build confidence."
    else:
        greeting += "What questions do you have? I'm here to help you understand this concept deeply."

    return greeting


def continue_tutor_conversation(
    conversation: Conversation,
    user_message: str
) -> str:
    """
    Continue an existing tutor conversation with a new user message.

    Args:
        conversation: Existing conversation object
        user_message: New message from the student

    Returns:
        The tutor's response
    """
    try:
        # Generate response
        tutor_response = generate_tutor_response(conversation, user_message)

        # Add messages to conversation
        conversation.add_message("user", user_message)
        conversation.add_message("assistant", tutor_response)

        logger.info(f"Continued conversation {conversation.conversation_id}")
        return tutor_response

    except Exception as e:
        logger.error(f"Error continuing tutor conversation: {e}")
        raise
