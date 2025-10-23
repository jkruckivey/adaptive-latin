"""
Roman Character Agent: Scenario-based Latin practice conversations

Handles immersive conversations with Roman characters to practice grammar.
Students interact with everyday Romans (merchants, students, poets) who
demonstrate Latin grammar in natural contexts.
"""

import anthropic
import json
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
# Scenario Management
# ============================================================================

def load_scenarios(concept_id: str) -> List[Dict[str, Any]]:
    """Load scenario definitions for a concept."""
    try:
        concept_dir = config.RESOURCE_BANK_DIR / concept_id
        scenarios_file = concept_dir / "scenarios.json"

        if not scenarios_file.exists():
            logger.warning(f"No scenarios found for {concept_id}")
            return []

        with open(scenarios_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scenarios = data.get("scenarios", [])
        logger.info(f"Loaded {len(scenarios)} scenarios for {concept_id}")
        return scenarios

    except Exception as e:
        logger.error(f"Error loading scenarios for {concept_id}: {e}")
        return []


def select_scenario(
    concept_id: str,
    learner_performance: Optional[Dict[str, Any]] = None,
    scenario_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Select an appropriate scenario based on student performance.

    Args:
        concept_id: The concept being studied
        learner_performance: Optional dict with recent scores/struggles
        scenario_id: Optional specific scenario to use

    Returns:
        Scenario dictionary or None if not found
    """
    try:
        scenarios = load_scenarios(concept_id)

        if not scenarios:
            return None

        # If specific scenario requested, return it
        if scenario_id:
            for scenario in scenarios:
                if scenario.get("scenario_id") == scenario_id:
                    logger.info(f"Selected scenario: {scenario_id}")
                    return scenario
            logger.warning(f"Scenario {scenario_id} not found")
            return None

        # Otherwise, select based on difficulty and performance
        if learner_performance:
            recent_score = learner_performance.get("recent_average_score", 0.7)

            # If struggling (score < 0.6), use beginner scenario
            if recent_score < 0.6:
                for scenario in scenarios:
                    if scenario.get("difficulty") == "beginner":
                        logger.info(f"Selected beginner scenario for struggling student")
                        return scenario

            # If doing well (score > 0.8), use intermediate scenario
            elif recent_score > 0.8:
                for scenario in scenarios:
                    if scenario.get("difficulty") == "beginner-intermediate":
                        logger.info(f"Selected intermediate scenario for confident student")
                        return scenario

        # Default: return first scenario
        logger.info(f"Selected default scenario: {scenarios[0].get('scenario_id')}")
        return scenarios[0]

    except Exception as e:
        logger.error(f"Error selecting scenario: {e}")
        return None


# ============================================================================
# System Prompt Loading and Formatting
# ============================================================================

def load_roman_system_prompt() -> str:
    """Load the Roman character system prompt template."""
    try:
        prompt_file = config.PROMPTS_DIR / "roman-system-prompt.md"

        if not prompt_file.exists():
            raise FileNotFound(f"Roman system prompt not found at {prompt_file}")

        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        logger.error(f"Error loading Roman system prompt: {e}")
        raise


def format_roman_system_prompt(
    scenario: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """
    Format the Roman system prompt with scenario and learner context.

    Args:
        scenario: The scenario dictionary
        context: Learner context (from build_conversation_context)

    Returns:
        Formatted system prompt string
    """
    try:
        # Load base prompt template
        template = load_roman_system_prompt()

        # Extract scenario details
        character_name = scenario.get("character_name", "Unknown")
        character_role = scenario.get("character_role", "Roman citizen")
        setting = scenario.get("setting", "Ancient Rome")
        personality = scenario.get("character_personality", "Friendly and helpful")

        # Format grammar focus
        grammar_focus_list = scenario.get("primary_grammar_focus", [])
        grammar_focus = "\n".join(f"- {item}" for item in grammar_focus_list)

        # Format learning goals
        learning_goals_list = scenario.get("learning_goals", [])
        learning_goals = "\n".join(f"- {item}" for item in learning_goals_list)
        learning_goals_detailed = "\n".join(f"{i+1}. {goal}" for i, goal in enumerate(learning_goals_list))

        # Format vocabulary list
        vocabulary = scenario.get("vocabulary_used", [])
        vocabulary_list = "\n".join(
            f"- {v.get('latin')} ({v.get('english')})"
            for v in vocabulary
        )
        vocabulary_examples = ", ".join(v.get("latin", "") for v in vocabulary[:3])

        # Get concept metadata
        concept_id = context.get("current_concept", "concept-001")
        try:
            metadata = load_concept_metadata(concept_id)
            concept_title = metadata.get("title", concept_id)
        except:
            concept_title = concept_id

        # Fill in template placeholders
        formatted_prompt = template.format(
            character_name=character_name,
            character_role=character_role,
            setting=setting,
            character_personality=personality,
            grammar_focus=grammar_focus,
            learning_goals=learning_goals,
            learning_goals_detailed=learning_goals_detailed,
            vocabulary_list=vocabulary_list,
            vocabulary_examples=vocabulary_examples,
            concept_title=concept_title
        )

        return formatted_prompt

    except Exception as e:
        logger.error(f"Error formatting Roman system prompt: {e}")
        raise


# ============================================================================
# Conversation Generation
# ============================================================================

def generate_roman_response(
    conversation: Conversation,
    user_message: str,
    temperature: float = 0.8
) -> str:
    """
    Generate a Roman character response using Claude API.

    Args:
        conversation: The conversation object with scenario in context
        user_message: The new message from the student
        temperature: Sampling temperature (0.8 for more creative/natural responses)

    Returns:
        The Roman character's response string
    """
    try:
        # Get scenario from conversation context
        scenario = conversation.scenario

        if not scenario:
            raise ValueError("No scenario found in conversation")

        # Build system prompt with scenario and learner context
        system_prompt = format_roman_system_prompt(scenario, conversation.context)

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

        logger.info(f"Generating Roman response for scenario {scenario.get('scenario_id')}")

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

        logger.info(f"Generated Roman response ({len(response_text)} chars)")
        return response_text

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "Ignosce mihi... (Forgive me...) I'm having trouble right now. Please try again in a moment."

    except Exception as e:
        logger.error(f"Error generating Roman response: {e}")
        return "Ignosce mihi... (Forgive me...) Something went wrong. Please try again."


# ============================================================================
# Conversation Management
# ============================================================================

def start_roman_conversation(
    learner_id: str,
    concept_id: str,
    scenario_id: Optional[str] = None,
    learner_performance: Optional[Dict[str, Any]] = None
) -> Conversation:
    """
    Start a new Roman character conversation.

    Args:
        learner_id: Unique identifier for the learner
        concept_id: Current concept being studied
        scenario_id: Optional specific scenario to use
        learner_performance: Optional performance data for scenario selection

    Returns:
        New Conversation object
    """
    try:
        from .conversations import Conversation, generate_conversation_id

        # Select appropriate scenario
        scenario = select_scenario(concept_id, learner_performance, scenario_id)

        if not scenario:
            raise ValueError(f"No scenarios available for {concept_id}")

        # Generate conversation ID
        conversation_id = generate_conversation_id(learner_id, "roman")

        # Build context
        context = build_conversation_context(learner_id, concept_id)

        # Create conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            learner_id=learner_id,
            conversation_type="roman",
            concept_id=concept_id,
            context=context,
            scenario=scenario,
            counts_toward_progress=True
        )

        # Add initial greeting from Roman character
        greeting = generate_roman_greeting(scenario)
        conversation.add_message("assistant", greeting)

        logger.info(f"Started Roman conversation {conversation_id} with {scenario.get('character_name')}")
        return conversation

    except Exception as e:
        logger.error(f"Error starting Roman conversation: {e}")
        raise


def generate_roman_greeting(scenario: Dict[str, Any]) -> str:
    """Generate the initial greeting from the Roman character."""
    character_name = scenario.get("character_name", "Unknown")
    greeting_latin = scenario.get("initial_greeting_latin", "Salvē!")
    greeting_translation = scenario.get("initial_greeting_translation", "Hello!")

    # Format greeting with translation
    greeting = f"{greeting_latin}\n\n[Translation: {greeting_translation}]\n\n"

    # Add context about the conversation
    setting = scenario.get("setting", "ancient Rome")
    greeting += f"(You find yourself in {setting}. {character_name} is speaking with you in Latin. "
    greeting += "You can respond in Latin or English - I'll help you with the Latin!)"

    return greeting


def continue_roman_conversation(
    conversation: Conversation,
    user_message: str
) -> str:
    """
    Continue an existing Roman conversation with a new user message.

    Args:
        conversation: Existing conversation object
        user_message: New message from the student

    Returns:
        The Roman character's response
    """
    try:
        # Generate response
        roman_response = generate_roman_response(conversation, user_message)

        # Add messages to conversation
        conversation.add_message("user", user_message)
        conversation.add_message("assistant", roman_response)

        logger.info(f"Continued Roman conversation {conversation.conversation_id}")
        return roman_response

    except Exception as e:
        logger.error(f"Error continuing Roman conversation: {e}")
        raise
