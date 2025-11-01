"""
Content Generation Request Builders

Extracted from agent.py to improve maintainability and testability.
Each function builds a specific prompt for Claude based on the learning stage.
"""

import random
import logging
from typing import Dict, Any, Optional, List
from .constants import (
    PREVIEW_READ_TIME_SECONDS,
    PREVIEW_CONTENT_TYPES,
    CUMULATIVE_REVIEW_CONCEPTS_COUNT
)

logger = logging.getLogger(__name__)


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input before including in AI prompts to prevent prompt injection.

    Args:
        text: The user input text to sanitize
        max_length: Maximum allowed length (default 1000 chars)

    Returns:
        Sanitized text safe for inclusion in prompts
    """
    if not isinstance(text, str):
        text = str(text)

    # Limit length to prevent prompt flooding
    text = text[:max_length]

    # Remove null bytes and control characters (except newlines/tabs)
    text = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127))

    # Escape common prompt injection patterns
    text = text.replace('```', '\\`\\`\\`')
    text = text.replace('###', '\\#\\#\\#')
    text = text.replace('<|', '\\<\\|')
    text = text.replace('|>', '\\|\\>')
    text = text.replace('[INST]', '\\[INST\\]')
    text = text.replace('[/INST]', '\\[/INST\\]')

    # Limit consecutive special characters to prevent pattern-based attacks
    import re
    text = re.sub(r'([!@#$%^&*()_+=\[\]{}|\\:;"\'<>,.?/~`-])\1{4,}', r'\1\1\1', text)

    return text


def generate_preview_request(learning_style: str) -> str:
    """
    Generate request for preview content based on learner's learning style.

    Args:
        learning_style: Learner's preferred learning style ('narrative', 'varied', 'adaptive')

    Returns:
        Prompt string for Claude
    """
    if learning_style == 'narrative':
        return (
            f"Generate a brief 'example-set' preview ({PREVIEW_READ_TIME_SECONDS}-second read) "
            "showing the concept through story-based examples. Keep it short - this is just a "
            "quick preview before assessment. Respond ONLY with the JSON object, no other text."
        )

    elif learning_style == 'varied':
        # Vary preview format including interactive widgets
        preview_type = random.choice(PREVIEW_CONTENT_TYPES)
        logger.info(f"Varied learning style - preview with: {preview_type}")

        if preview_type == 'paradigm-table':
            return (
                f"Generate a brief 'paradigm-table' preview ({PREVIEW_READ_TIME_SECONDS}-second scan) "
                "showing the key grammatical patterns for this concept. Include a very short explanation "
                "(2-3 sentences max). This is a quick preview before assessment. Respond ONLY with the "
                "JSON object, no other text."
            )
        elif preview_type == 'declension-explorer':
            return (
                "Generate a 'declension-explorer' interactive widget preview for quick exploration of "
                "the concept. Show a relevant noun declension with brief explanation. This is a quick "
                "interactive preview before assessment. Respond ONLY with the JSON object, no other text."
            )
        elif preview_type == 'example-set':
            return (
                "Generate a brief 'example-set' preview showing the concept through varied examples. "
                "Keep it short - this is just a quick preview before assessment. Respond ONLY with the "
                "JSON object, no other text."
            )
        else:  # lesson
            return (
                f"Generate a brief 'lesson' preview ({PREVIEW_READ_TIME_SECONDS}-second read) explaining "
                "the core concept. Keep it short - this is just a quick preview before assessment. "
                "Respond ONLY with the JSON object, no other text."
            )

    elif learning_style == 'adaptive':
        return (
            f"Generate a brief 'lesson' preview ({PREVIEW_READ_TIME_SECONDS}-second read) explaining "
            "the core concept and key patterns. Keep it short - this is just a conceptual foundation "
            "before assessment. Respond ONLY with the JSON object, no other text."
        )

    else:
        return (
            f"Generate a brief 'lesson' preview ({PREVIEW_READ_TIME_SECONDS}-second read) explaining "
            "the core concept. Keep it short - this is just a conceptual foundation before assessment. "
            "Respond ONLY with the JSON object, no other text."
        )


def generate_diagnostic_request(is_cumulative: bool, cumulative_concepts: List[str] = None) -> str:
    """
    Generate request for diagnostic multiple-choice question.

    Args:
        is_cumulative: Whether this is a cumulative review question
        cumulative_concepts: List of concept IDs to integrate (for cumulative review)

    Returns:
        Prompt string for Claude
    """
    if is_cumulative and cumulative_concepts:
        return (
            f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates the concepts "
            f"listed above. The scenario should naturally require applying knowledge from at least "
            f"{len(cumulative_concepts) if len(cumulative_concepts) > 1 else 2} of those concepts. "
            f"Include a rich Roman context. Mark this as is_cumulative: true in the metadata. "
            f"Respond ONLY with the JSON object, no other text."
        )
    else:
        return (
            "Generate a 'multiple-choice' diagnostic question with a NEW scenario (different from "
            "any shown above). Include a rich Roman context (inscription, letter, etc.). Respond "
            "ONLY with the JSON object, no other text."
        )


def generate_practice_request(is_cumulative: bool, cumulative_concepts: List[str] = None) -> str:
    """
    Generate request for practice question (next diagnostic after correct answer).

    Args:
        is_cumulative: Whether this is a cumulative review question
        cumulative_concepts: List of concept IDs to integrate (for cumulative review)

    Returns:
        Prompt string for Claude
    """
    if is_cumulative and cumulative_concepts:
        return (
            f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates concepts from "
            f"the list above. Create a scenario that requires applying knowledge from at least "
            f"{len(cumulative_concepts) if len(cumulative_concepts) > 1 else 2} of those concepts together. "
            f"Use a different Roman setting. Mark this as is_cumulative: true in the metadata. "
            f"Respond ONLY with the JSON object, no other text."
        )
    else:
        return (
            "Generate a 'multiple-choice' diagnostic question with a COMPLETELY DIFFERENT scenario "
            "from those listed above. Vary the context: use different Latin words, different Roman "
            "settings (forum, bath, temple, road sign, etc.), different grammatical cases. Increase "
            "difficulty slightly. Respond ONLY with the JSON object, no other text."
        )


def build_question_context_string(question_context: Optional[Dict[str, Any]]) -> str:
    """
    Build a formatted string describing the question they just answered.

    Args:
        question_context: Dict with scenario, question, user_answer, correct_answer, options

    Returns:
        Formatted context string for the prompt, or empty string if no context
    """
    if not question_context:
        return ""

    # Sanitize all user-facing content
    scenario = sanitize_user_input(question_context.get('scenario', ''))
    question = sanitize_user_input(question_context.get('question', ''))
    user_ans_idx = question_context.get('user_answer', 'unknown')
    correct_ans_idx = question_context.get('correct_answer', 'unknown')
    options = question_context.get('options', [])

    # Get the actual text of what they chose vs correct answer
    user_answer_text = (
        sanitize_user_input(options[user_ans_idx])
        if isinstance(user_ans_idx, int) and options and user_ans_idx < len(options)
        else str(user_ans_idx)
    )
    correct_answer_text = (
        sanitize_user_input(options[correct_ans_idx])
        if isinstance(correct_ans_idx, int) and options and correct_ans_idx < len(options)
        else str(correct_ans_idx)
    )

    context = (
        f"\n\n=== THE QUESTION THEY JUST ANSWERED INCORRECTLY ===\n\n"
        f"Scenario: {scenario}\n\n"
        f"Question: {question}\n\n"
        f"THEY CHOSE: '{user_answer_text}' (Option {user_ans_idx})\n\n"
        f"CORRECT ANSWER: '{correct_answer_text}' (Option {correct_ans_idx})\n\n"
        f"All Options:\n"
    )

    for i, opt in enumerate(options):
        marker = "✓ CORRECT" if i == correct_ans_idx else ("✗ THEY CHOSE THIS" if i == user_ans_idx else "")
        sanitized_opt = sanitize_user_input(opt)
        context += f"{i}. {sanitized_opt} {marker}\n"

    context += "\n"
    return context


def generate_remediation_request(
    question_context: Optional[Dict[str, Any]],
    confidence: Optional[int],
    remediation_type: str,
    learning_style: str
) -> str:
    """
    Generate request for remediation content after incorrect answer.

    Args:
        question_context: Details about the question they got wrong
        confidence: Their confidence level (1-4)
        remediation_type: Type of remediation needed
        learning_style: Learner's preferred style

    Returns:
        Prompt string for Claude
    """
    # Build context about what they answered wrong
    last_question_context = build_question_context_string(question_context)

    # Determine preferred content format based on learner style
    preferred_content_type = _select_remediation_content_type(learning_style)

    # Generate request based on remediation type and content preference
    if remediation_type == "full_calibration":
        return _build_full_calibration_request(
            last_question_context,
            confidence,
            preferred_content_type
        )
    elif remediation_type == "supportive":
        return _build_supportive_request(
            last_question_context,
            confidence,
            preferred_content_type
        )
    else:
        return _build_default_remediation_request(
            last_question_context,
            preferred_content_type
        )


def _select_remediation_content_type(learning_style: str) -> str:
    """Select appropriate content type for remediation based on learning style."""
    if learning_style == 'narrative':
        return 'example-set'
    elif learning_style == 'varied':
        # Vary content type - alternate between different formats including interactive widgets
        content_type = random.choice([
            'paradigm-table', 'example-set', 'lesson',
            'declension-explorer', 'word-order-manipulator'
        ])
        logger.info(f"Varied learning style - selected: {content_type}")
        return content_type
    elif learning_style == 'adaptive':
        return 'lesson'
    else:
        return 'lesson'


def _build_full_calibration_request(
    context: str,
    confidence: Optional[int],
    content_type: str
) -> str:
    """Build request for full calibration remediation (overconfident learner)."""
    base_intro = f"The student answered incorrectly with {confidence}/4 confidence (overconfident).{context}"

    if content_type == 'paradigm-table':
        return (
            f"{base_intro}Generate a 'paradigm-table' that: 1) Shows the complete declension table "
            f"for the grammar concept they missed, 2) Highlights the specific form they should have chosen, "
            f"3) Includes explanation text that STARTS with: 'You chose [their answer], but looking at the "
            f"complete paradigm, the correct answer is [correct answer] because...' 4) Uses their interests "
            f"in the explanation. Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'declension-explorer':
        return (
            f"{base_intro}Generate a 'declension-explorer' interactive widget that: 1) Shows all forms "
            f"for the noun/declension relevant to their mistake, 2) Sets highlightCase to the case they "
            f"got wrong, 3) Includes explanation text that STARTS with: 'You chose [their answer], but "
            f"let's explore the full paradigm. The correct answer is [correct answer] because...' "
            f"Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'example-set':
        return (
            f"{base_intro}Generate an 'example-set' (NOT a lesson, NOT a table) that: 1) Shows 3-4 "
            f"contextual examples demonstrating the correct grammar concept, 2) Each example includes "
            f"Latin, translation, and notes explaining why it's correct, 3) Uses their interests from "
            f"the Learner Profile in the examples, 4) Addresses their specific misconception. "
            f"CRITICAL: type must be 'example-set'. Respond ONLY with the JSON object, no other text."
        )
    else:  # lesson or other
        return (
            f"{base_intro}Generate a 'lesson' (NOT a table) that: 1) STARTS with: 'You chose [their answer], "
            f"which suggests [what misconception this reveals]. However, the correct answer is [correct answer] "
            f"because...' 2) Explains the SPECIFIC grammatical concept they misunderstood, 3) Provides 2-3 "
            f"examples using their interests (see Learner Profile above - ACTUALLY use those topics in your "
            f"examples, not generic ones!), 4) Includes calibration feedback about recognizing when to be "
            f"less certain. CRITICAL: The examples MUST relate to the specific interests mentioned in the "
            f"Learner Profile. Respond ONLY with the JSON object, no other text."
        )


def _build_supportive_request(
    context: str,
    confidence: Optional[int],
    content_type: str
) -> str:
    """Build request for supportive remediation (aware of uncertainty)."""
    base_intro = f"The student answered incorrectly with {confidence}/4 confidence (aware of uncertainty).{context}"

    if content_type == 'paradigm-table':
        return (
            f"{base_intro}Generate a supportive 'paradigm-table' with: 1) Complete declension table, "
            f"2) Encouraging explanation that validates their awareness of difficulty, 3) Clear marking "
            f"of the correct answer. Be gentle. Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'example-set':
        return (
            f"{base_intro}Generate a supportive 'example-set' (NOT a table) with: 1) 3-4 encouraging "
            f"examples using their interests, 2) Each example shows correct usage with Latin, translation, "
            f"and notes, 3) Validates their awareness of difficulty. CRITICAL: type must be 'example-set'. "
            f"Be gentle. Respond ONLY with the JSON object, no other text."
        )
    else:  # lesson or other
        return (
            f"{base_intro}Generate a supportive 'lesson' (NOT a table) that: 1) Explains: 'You chose "
            f"[their answer], but the correct answer is [correct answer] because...' 2) Directly addresses "
            f"why their specific choice was wrong, 3) Provides 2-3 encouraging examples using their interests "
            f"from the Learner Profile (ACTUALLY use those topics!). CRITICAL: type must be 'lesson'. "
            f"Be gentle and encouraging. Respond ONLY with the JSON object, no other text."
        )


def _build_default_remediation_request(context: str, content_type: str) -> str:
    """Build request for default remediation."""
    if content_type == 'example-set':
        return (
            f"Generate an 'example-set' (NOT a table) to reinforce the concept from the most recent "
            f"question.{context}Show 3-4 examples using their interests. Each example has Latin, "
            f"translation, and notes. CRITICAL: type must be 'example-set'. Respond ONLY with the "
            f"JSON object, no other text."
        )
    else:  # lesson or other
        return (
            f"Generate a brief 'lesson' (NOT a table) to clarify the concept tested in the most recent "
            f"question.{context}Start by explaining: 'You chose [their answer], but the correct answer "
            f"is [correct answer].' Then briefly explain the specific concept and provide 1-2 examples "
            f"using their interests (see Learner Profile). CRITICAL: type must be 'lesson'. Respond "
            f"ONLY with the JSON object, no other text."
        )


def generate_reinforcement_request(
    question_context: Optional[Dict[str, Any]],
    confidence: Optional[int],
    learning_style: str
) -> str:
    """
    Generate request for reinforcement content (correct but low confidence).

    Args:
        question_context: Details about the question they answered correctly
        confidence: Their confidence level (1-4)
        learning_style: Learner's preferred style

    Returns:
        Prompt string for Claude
    """
    # Build context - they answered correctly this time
    last_question_context = ""
    if question_context:
        scenario = sanitize_user_input(question_context.get('scenario', ''))
        question = sanitize_user_input(question_context.get('question', ''))
        correct_ans_idx = question_context.get('correct_answer', 'unknown')
        options = question_context.get('options', [])

        correct_answer_text = (
            sanitize_user_input(options[correct_ans_idx])
            if isinstance(correct_ans_idx, int) and options and correct_ans_idx < len(options)
            else str(correct_ans_idx)
        )

        last_question_context = (
            f"\n\n=== THE QUESTION THEY JUST ANSWERED CORRECTLY (but with low confidence) ===\n\n"
            f"Scenario: {scenario}\n\n"
            f"Question: {question}\n\n"
            f"THEIR ANSWER: '{correct_answer_text}' (Option {correct_ans_idx}) ✓ CORRECT\n\n"
        )

    # Brief reinforcement for correct but uncertain answers - adapt format to preference
    if learning_style == 'narrative':
        return (
            f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident)."
            f"{last_question_context}Generate a brief 'example-set' (NOT a table) with story-based "
            f"examples that validates their answer and builds confidence. CRITICAL: type must be "
            f"'example-set'. Keep it short - they already know this! Respond ONLY with the JSON "
            f"object, no other text."
        )
    elif learning_style == 'varied':
        # Vary content type for reinforcement too
        reinforce_type = random.choice(['paradigm-table', 'example-set'])
        logger.info(f"Varied learning style - reinforce with: {reinforce_type}")

        if reinforce_type == 'paradigm-table':
            return (
                f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident)."
                f"{last_question_context}Generate a brief 'paradigm-table' showing the pattern they "
                f"correctly identified. Include encouraging explanation. Keep it short - they already "
                f"know this! Respond ONLY with the JSON object, no other text."
            )
        else:
            return (
                f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident)."
                f"{last_question_context}Generate a brief 'example-set' (NOT a table) that validates "
                f"their answer and builds confidence. CRITICAL: type must be 'example-set'. Keep it "
                f"short - they already know this! Respond ONLY with the JSON object, no other text."
            )
    else:
        # adaptive or default
        return (
            f"The student answered CORRECTLY but with only {confidence}/4 confidence (underconfident)."
            f"{last_question_context}Generate a brief 'example-set' (NOT a table) that validates their "
            f"answer to THAT specific question and builds confidence. CRITICAL: type must be 'example-set'. "
            f"Keep it short - they already know this! Respond ONLY with the JSON object, no other text."
        )
