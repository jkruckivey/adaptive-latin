"""
Content Generation Request Builders

Extracted from agent.py to improve maintainability and testability.
Each function builds a specific prompt for Claude based on the learning stage.
"""

import json
import random
import logging
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from .config import config
from .constants import (
    PREVIEW_READ_TIME_SECONDS,
    PREVIEW_CONTENT_TYPES,
    CUMULATIVE_REVIEW_CONCEPTS_COUNT
)

logger = logging.getLogger(__name__)

# Initialize Anthropic client for AI generation functions
client = Anthropic(api_key=config.ANTHROPIC_API_KEY)


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
                "showing the key patterns for this concept. Include a very short explanation "
                "(2-3 sentences max). This is a quick preview before assessment. Respond ONLY with the "
                "JSON object, no other text."
            )
        elif preview_type == 'declension-explorer':
            return (
                "Generate a 'declension-explorer' interactive widget preview for quick exploration of "
                "the concept. Show a relevant example with brief explanation. This is a quick "
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


def generate_diagnostic_request(
    is_cumulative: bool,
    cumulative_concepts: List[str] = None,
    difficulty: str = "appropriate"
) -> str:
    """
    Generate request for diagnostic multiple-choice question.

    Args:
        is_cumulative: Whether this is a cumulative review question
        cumulative_concepts: List of concept IDs to integrate (for cumulative review)
        difficulty: Question difficulty level ('easier', 'appropriate', 'harder')

    Returns:
        Prompt string for Claude
    """
    # Build difficulty instruction
    difficulty_instructions = {
        "easier": (
            "Use FUNDAMENTAL vocabulary and the most BASIC forms. "
            "Provide clearer context clues. Focus on recognition over production. "
            "Make distractors obviously wrong. "
        ),
        "appropriate": "",
        "harder": (
            "Use more complex vocabulary and varied forms. "
            "Require deeper analysis. Include subtle distractors. "
            "Challenge the learner with authentic examples. "
        )
    }

    difficulty_instruction = difficulty_instructions.get(difficulty, "")

    if is_cumulative and cumulative_concepts:
        return (
            f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates the concepts "
            f"listed above. The scenario should naturally require applying knowledge from at least "
            f"{len(cumulative_concepts) if len(cumulative_concepts) > 1 else 2} of those concepts. "
            f"{difficulty_instruction}"
            f"Include a rich contextual scenario. Mark this as is_cumulative: true in the metadata. "
            f"Respond ONLY with the JSON object, no other text."
        )
    else:
        return (
            f"Generate a 'multiple-choice' diagnostic question with a NEW scenario (different from "
            f"any shown above). {difficulty_instruction}"
            f"Include a rich contextual scenario. Respond "
            f"ONLY with the JSON object, no other text."
        )


def generate_practice_request(
    is_cumulative: bool,
    cumulative_concepts: List[str] = None,
    difficulty: str = "appropriate"
) -> str:
    """
    Generate request for practice question (next diagnostic after correct answer).

    Args:
        is_cumulative: Whether this is a cumulative review question
        cumulative_concepts: List of concept IDs to integrate (for cumulative review)
        difficulty: Question difficulty level ('easier', 'appropriate', 'harder')

    Returns:
        Prompt string for Claude
    """
    # Build difficulty instruction
    difficulty_instructions = {
        "easier": (
            "Use FUNDAMENTAL vocabulary and the most BASIC forms. "
            "Provide clearer context clues. Focus on recognition over production. "
            "Make distractors obviously wrong. "
        ),
        "appropriate": "Increase difficulty slightly. ",
        "harder": (
            "Use more complex vocabulary and varied forms. "
            "Require deeper analysis. Include subtle distractors. "
            "Challenge the learner with authentic examples. "
            "Significantly increase difficulty. "
        )
    }

    difficulty_instruction = difficulty_instructions.get(difficulty, "Increase difficulty slightly. ")

    if is_cumulative and cumulative_concepts:
        return (
            f"Generate a 'multiple-choice' CUMULATIVE REVIEW question that integrates concepts from "
            f"the list above. Create a scenario that requires applying knowledge from at least "
            f"{len(cumulative_concepts) if len(cumulative_concepts) > 1 else 2} of those concepts together. "
            f"{difficulty_instruction}"
            f"Use a different contextual scenario. Mark this as is_cumulative: true in the metadata. "
            f"Respond ONLY with the JSON object, no other text."
        )
    else:
        return (
            f"Generate a 'multiple-choice' diagnostic question with a COMPLETELY DIFFERENT scenario "
            f"from those listed above. {difficulty_instruction}"
            f"Vary the context: use different vocabulary, different scenarios, different aspects of the concept. "
            f"Respond ONLY with the JSON object, no other text."
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
        # Vary content type - alternate between different formats
        content_type = random.choice([
            'paradigm-table', 'example-set', 'lesson'
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
            f"{base_intro}Generate a 'paradigm-table' that: 1) Shows a complete structured table "
            f"of all variations/forms for the concept they missed, 2) Highlights the specific item they should have chosen, "
            f"3) Includes explanation text that STARTS with: 'You chose [their answer], but looking at the "
            f"complete table, the correct answer is [correct answer] because...' 4) Uses their interests "
            f"in the explanation. 5) Use appropriate headers for the subject matter (not Latin-specific terms). "
            f"Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'declension-explorer':
        return (
            f"{base_intro}Generate a 'declension-explorer' interactive widget that: 1) Shows all forms "
            f"relevant to their mistake, 2) Highlights the specific form they got wrong, 3) Includes "
            f"explanation text that STARTS with: 'You chose [their answer], but let's explore the complete "
            f"set of variations. The correct answer is [correct answer] because...' "
            f"Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'example-set':
        return (
            f"{base_intro}Generate an 'example-set' (NOT a lesson, NOT a table) that: 1) Shows 3-4 "
            f"contextual examples demonstrating the correct concept, 2) Each example includes "
            f"source material, explanation/translation, and notes explaining why it's correct, 3) Uses their interests from "
            f"the Learner Profile in the examples, 4) Addresses their specific misconception. "
            f"CRITICAL: type must be 'example-set'. Respond ONLY with the JSON object, no other text."
        )
    else:  # lesson or other
        return (
            f"{base_intro}Generate a 'lesson' (NOT a table) that: 1) STARTS with: 'You chose [their answer], "
            f"which suggests [what misconception this reveals]. However, the correct answer is [correct answer] "
            f"because...' 2) Explains the SPECIFIC concept they misunderstood, 3) Provides 2-3 "
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
            f"{base_intro}Generate a supportive 'paradigm-table' with: 1) Complete reference table, "
            f"2) Encouraging explanation that validates their awareness of difficulty, 3) Clear marking "
            f"of the correct answer. Be gentle. Respond ONLY with the JSON object, no other text."
        )
    elif content_type == 'example-set':
        return (
            f"{base_intro}Generate a supportive 'example-set' (NOT a table) with: 1) 3-4 encouraging "
            f"examples using their interests, 2) Each example shows correct usage with source material, explanation, "
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
            f"question.{context}Show 3-4 examples using their interests. Each example has source material, "
            f"explanation, and notes. CRITICAL: type must be 'example-set'. Respond ONLY with the "
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


def generate_hint_request(
    question_context: Dict[str, Any],
    hint_level: str,
    concept_id: str
) -> str:
    """
    Generate request for a hint (practice mode only).

    Args:
        question_context: Details about the current question
        hint_level: 'gentle' (indirect), 'direct' (more specific), or 'answer' (show solution)
        concept_id: Current concept ID for context

    Returns:
        Prompt string for Claude
    """
    scenario = sanitize_user_input(question_context.get('scenario', ''))
    question = sanitize_user_input(question_context.get('question', ''))
    options = question_context.get('options', [])
    correct_answer = question_context.get('correct_answer', None)

    # Build options text
    options_text = ""
    if options:
        options_text = "\nOptions:\n"
        for i, opt in enumerate(options):
            options_text += f"{i}. {sanitize_user_input(opt)}\n"

    question_info = (
        f"Concept: {concept_id}\n\n"
        f"Scenario: {scenario}\n\n"
        f"Question: {question}"
        f"{options_text}"
    )

    if hint_level == "gentle":
        # Gentle hint - nudge in right direction without revealing answer
        return (
            f"PRACTICE MODE HINT REQUEST (Gentle Level)\n\n"
            f"The learner is stuck on this question and requested a gentle hint:\n\n"
            f"{question_info}\n\n"
            f"Generate a gentle hint that:\n"
            f"- Points them toward the right concept WITHOUT revealing the answer\n"
            f"- Asks a guiding question (e.g., 'What pattern do you notice here?')\n"
            f"- Reminds them of a relevant pattern\n"
            f"- Keeps them thinking actively\n\n"
            f"Return ONLY plain text (not JSON), max 2-3 sentences."
        )

    elif hint_level == "direct":
        # Direct hint - more specific guidance
        return (
            f"PRACTICE MODE HINT REQUEST (Direct Level)\n\n"
            f"The learner is stuck on this question and requested a more direct hint:\n\n"
            f"{question_info}\n\n"
            f"Generate a direct hint that:\n"
            f"- Narrows down to the specific feature being tested\n"
            f"- Explains what to look for (e.g., 'The key indicator here is...')\n"
            f"- Eliminates clearly wrong options if multiple choice\n"
            f"- Still lets them make the final connection\n\n"
            f"Return ONLY plain text (not JSON), max 3-4 sentences."
        )

    else:  # answer
        # Show answer with explanation
        correct_text = ""
        if isinstance(correct_answer, int) and options and correct_answer < len(options):
            correct_text = sanitize_user_input(options[correct_answer])

        return (
            f"PRACTICE MODE ANSWER REVEAL\n\n"
            f"The learner requested to see the answer:\n\n"
            f"{question_info}\n\n"
            f"The correct answer is: {correct_text} (Option {correct_answer})\n\n"
            f"Generate a clear explanation (plain text, not JSON) that:\n"
            f"- States why this is the correct answer\n"
            f"- Explains the reasoning behind it\n"
            f"- Shows how to identify this pattern in future\n"
            f"- Encourages them to try another practice question\n\n"
            f"Return ONLY plain text (not JSON), max 4-5 sentences."
        )


# ========================================
# AI-Powered Learning Outcome Generation
# ========================================

def generate_learning_outcomes(
    description: str,
    taxonomy: str = 'blooms',
    level: str = 'course',
    count: int = 5,
    existing_outcomes: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate learning outcomes using AI based on course description.
    
    Args:
        description: Course/module description or topic
        taxonomy: Taxonomy to use ('blooms', 'finks', 'qm')
        level: Level of outcomes ('course', 'module', 'concept')
        count: Number of outcomes to generate
        existing_outcomes: Existing outcomes to avoid duplication
        
    Returns:
        List of outcome dictionaries with text and metadata
    """
    try:
        # Build prompt based on taxonomy
        taxonomy_guidance = _get_taxonomy_guidance(taxonomy, level)
        
        existing_text = ""
        if existing_outcomes:
            existing_text = f"\n\nExisting outcomes (avoid duplication):\n" + "\n".join(f"- {o}" for o in existing_outcomes)
        
        prompt = f"""Generate {count} high-quality learning outcomes for a {level}-level course component.

Description: {description}

{taxonomy_guidance}

Requirements:
- Each outcome should be measurable and action-oriented
- Start with appropriate action verbs for the taxonomy level
- Be specific and concrete about what learners will achieve
- Align with {taxonomy.title()} taxonomy principles{existing_text}

Return a JSON array of outcomes, where each outcome is an object with:
- "text": the learning outcome statement
- "action_verb": the primary action verb used
- "taxonomy_level": the level in the taxonomy (e.g., "analyze", "apply")
- "domain": cognitive/affective/psychomotor domain

Example format:
[
  {{
    "text": "Analyze complex datasets to identify patterns and trends",
    "action_verb": "analyze",
    "taxonomy_level": "analyze",
    "domain": "cognitive"
  }}
]

Return ONLY the JSON array, no other text."""

        # Call Claude API
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        response_text = response.content[0].text.strip()
        
        # Extract JSON if wrapped in code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        outcomes = json.loads(response_text)
        
        logger.info(f"Generated {len(outcomes)} learning outcomes for {level}")
        return outcomes
        
    except Exception as e:
        logger.error(f"Error generating learning outcomes: {e}")
        # Return fallback outcomes
        return [{
            "text": f"Complete the learning objectives for this {level}",
            "action_verb": "complete",
            "taxonomy_level": "understand",
            "domain": "cognitive"
        }]


def generate_module_learning_outcomes(
    module_title: str,
    course_title: str,
    course_learning_outcomes: List[str],
    domain: str,
    taxonomy: str = 'blooms',
    count: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate module-specific learning outcomes that ladder up to course outcomes.
    
    Args:
        module_title: Title of the module
        course_title: Title of the parent course
        course_learning_outcomes: Course-level outcomes to align with
        domain: Subject domain (e.g., 'latin-grammar', 'excel')
        taxonomy: Taxonomy to use
        count: Number of outcomes to generate
        
    Returns:
        List of outcome dictionaries
    """
    try:
        clo_text = "\n".join(f"- {o}" for o in course_learning_outcomes)
        taxonomy_guidance = _get_taxonomy_guidance(taxonomy, 'module')
        
        prompt = f"""Generate {count} module learning outcomes (MLOs) for this module.

Course: {course_title}
Module: {module_title}
Domain: {domain}

Course Learning Outcomes (CLOs):
{clo_text}

{taxonomy_guidance}

Requirements:
- Each MLO should contribute to one or more CLOs
- MLOs should be more specific than CLOs but still substantial
- Use appropriate {taxonomy.title()} taxonomy action verbs
- Be measurable and achievable within a module timeframe
- Consider the domain: {domain}

Return a JSON array where each outcome has:
- "text": the outcome statement
- "action_verb": primary action verb
- "taxonomy_level": level in taxonomy
- "aligns_with_clo": index(es) of CLO(s) it supports (array of integers)

Return ONLY the JSON array."""

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        outcomes = json.loads(response_text)
        logger.info(f"Generated {len(outcomes)} module outcomes for '{module_title}'")
        return outcomes
        
    except Exception as e:
        logger.error(f"Error generating module outcomes: {e}")
        return [{
            "text": f"Master the concepts in {module_title}",
            "action_verb": "master",
            "taxonomy_level": "apply",
            "aligns_with_clo": [0]
        }]


def generate_concept_learning_objectives(
    concept_title: str,
    module_title: str,
    module_learning_outcomes: List[str],
    course_title: str,
    domain: str,
    taxonomy: str = 'blooms',
    count: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate concept-specific learning objectives that support module outcomes.
    
    Args:
        concept_title: Title of the concept
        module_title: Title of the parent module
        module_learning_outcomes: Module-level outcomes to align with
        course_title: Title of the course
        domain: Subject domain
        taxonomy: Taxonomy to use
        count: Number of objectives to generate
        
    Returns:
        List of objective dictionaries
    """
    try:
        mlo_text = "\n".join(f"- {o}" for o in module_learning_outcomes)
        taxonomy_guidance = _get_taxonomy_guidance(taxonomy, 'concept')
        
        prompt = f"""Generate {count} concept learning objectives for this specific concept.

Course: {course_title}
Module: {module_title}
Concept: {concept_title}
Domain: {domain}

Module Learning Outcomes (MLOs):
{mlo_text}

{taxonomy_guidance}

Requirements:
- Each objective should be very specific and focused
- Objectives should be achievable in a single lesson/concept
- Use concrete, measurable action verbs from {taxonomy.title()} taxonomy
- Should build toward the module outcomes
- Be appropriate for the domain: {domain}

Return a JSON array where each objective has:
- "text": the objective statement
- "action_verb": primary action verb
- "taxonomy_level": level in taxonomy
- "supports_mlo": index(es) of MLO(s) it supports (array of integers)

Return ONLY the JSON array."""

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        objectives = json.loads(response_text)
        logger.info(f"Generated {len(objectives)} objectives for concept '{concept_title}'")
        return objectives
        
    except Exception as e:
        logger.error(f"Error generating concept objectives: {e}")
        return [{
            "text": f"Understand and apply {concept_title}",
            "action_verb": "apply",
            "taxonomy_level": "apply",
            "supports_mlo": [0]
        }]


def _get_taxonomy_guidance(taxonomy: str, level: str) -> str:
    """Get taxonomy-specific guidance for outcome generation."""
    
    if taxonomy == 'blooms':
        if level == 'course':
            return """Use Bloom's Taxonomy (revised):
- Higher-order thinking: Create, Evaluate, Analyze
- Mid-level: Apply, Understand
- Foundation: Remember

Focus on higher-order outcomes for course level."""
        elif level == 'module':
            return """Use Bloom's Taxonomy (revised):
- Emphasize: Analyze, Apply, Evaluate
- Support with: Understand
- Avoid: Remember (too basic for module level)

Module outcomes should involve application and analysis."""
        else:  # concept
            return """Use Bloom's Taxonomy (revised):
- Focus on: Apply, Understand, Analyze
- Can include: Remember (for foundational concepts)
- Build toward higher-order thinking

Concept objectives should be concrete and specific."""
    
    elif taxonomy == 'finks':
        return """Use Fink's Taxonomy of Significant Learning:
- Foundational Knowledge: Understanding and remembering information
- Application: Skills, thinking, managing projects
- Integration: Connecting ideas
- Human Dimension: Learning about oneself and others
- Caring: Developing new feelings, interests, values
- Learning How to Learn: Becoming a better student"""
    
    elif taxonomy == 'qm':
        return """Follow Quality Matters standards:
- Measurable and clear
- Aligned with course/module activities and assessments
- Appropriate for the level of the course
- Focused on what learners will accomplish"""
    
    else:
        return f"Use {taxonomy} taxonomy principles for learning outcome design."


def generate_simulation_content(
    simulation_type: str,
    course_format: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate interactive simulation content.
    
    Args:
        simulation_type: Type of simulation to generate
        course_format: Format/domain of the course
        data: Simulation parameters and context
        
    Returns:
        Simulation content dictionary
    """
    try:
        prompt = f"""Generate an interactive {simulation_type} simulation for a {course_format} course.

Context: {json.dumps(data, indent=2)}

Create an engaging simulation that:
- Presents a realistic scenario
- Requires learner decision-making
- Provides meaningful feedback
- Teaches through doing

Return a JSON object with:
- "scenario": the scenario description
- "options": array of choices
- "feedback": object mapping choices to feedback
- "learning_point": key takeaway

Return ONLY the JSON object."""

        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        simulation = json.loads(response_text)
        logger.info(f"Generated {simulation_type} simulation")
        return simulation
        
    except Exception as e:
        logger.error(f"Error generating simulation: {e}")
        return {
            "scenario": "Error generating simulation",
            "options": [],
            "feedback": {},
            "learning_point": "Please try again"
        }
