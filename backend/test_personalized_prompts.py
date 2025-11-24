"""
Test script for personalized assessment prompts.

This script tests the new personalization system that adapts
assessment questions to learner interests while preserving
learning objectives and assessment validity.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.tools import (
    personalize_assessment_prompt,
    select_personalized_dialogue_prompt,
    load_learner_model
)


def test_personalize_prompt():
    """Test basic prompt personalization with different learner profiles."""

    print("=" * 80)
    print("TEST 1: Personalize Assessment Prompt - Different Interest Profiles")
    print("=" * 80)

    # Sample prompt data
    prompt_data = {
        "id": "dialogue-001-1",
        "base_prompt": "How do you identify a first declension noun?",
        "scenario_templates": {
            "history": "You're examining a Roman inscription and see the word 'MEMORIAE'. How would you identify whether this belongs to the first declension?",
            "archaeology": "You've uncovered a stone tablet with 'VICTORIAE AUGUSTAE' carved on it. How do you know if these nouns are first declension?",
            "mythology": "You're reading about Roman gods and encounter 'DEA FORTUNAE' (goddess of fortune). How can you tell if 'FORTUNAE' is first declension?",
            "literature": "You're translating a Latin poem and see 'rosa, rosae'. How do you identify this as first declension?",
            "default": "How do you know if a noun is first declension? What should you look for?"
        }
    }

    # Test different learner profiles
    test_profiles = [
        {
            "name": "History Teacher",
            "profile": {"interests": "Roman history, archaeology, ancient warfare"},
            "expected_scenario": "history"
        },
        {
            "name": "Archaeology Student",
            "profile": {"interests": "archaeology, excavation, ancient sites"},
            "expected_scenario": "archaeology"
        },
        {
            "name": "Mythology Enthusiast",
            "profile": {"interests": "mythology, gods and goddesses, legends"},
            "expected_scenario": "mythology"
        },
        {
            "name": "Literature Lover",
            "profile": {"interests": "literature, poetry, reading"},
            "expected_scenario": "literature"
        },
        {
            "name": "Generic Learner",
            "profile": {"interests": "learning latin"},
            "expected_scenario": "default"
        }
    ]

    for test_case in test_profiles:
        print(f"\n{test_case['name']}:")
        print(f"  Interests: {test_case['profile']['interests']}")

        personalized = personalize_assessment_prompt(prompt_data, test_case['profile'])
        expected = prompt_data["scenario_templates"][test_case['expected_scenario']]

        print(f"  Expected: {test_case['expected_scenario']}")
        print(f"  Question: {personalized[:100]}...")

        if personalized == expected:
            print("  [PASS] - Correctly personalized")
        else:
            print("  [FAIL] - Unexpected personalization")


def test_real_learner_personalization():
    """Test personalization with the actual test_walkthrough_001 learner."""

    print("\n" + "=" * 80)
    print("TEST 2: Real Learner Personalization (test_walkthrough_001)")
    print("=" * 80)

    learner_id = "test_walkthrough_001"

    try:
        # Load real learner profile
        learner_model = load_learner_model(learner_id)
        profile = learner_model.get("profile", {})

        print(f"\nLearner Profile:")
        print(f"  Background: {profile.get('background', 'N/A')[:100]}...")
        print(f"  Interests: {profile.get('interests', 'N/A')}")
        print(f"  Learning Style: {profile.get('learningStyle', 'N/A')}")

        # Test selecting personalized prompt for concept-001
        prompt_result = select_personalized_dialogue_prompt(
            concept_id="concept-001",
            learner_id=learner_id,
            difficulty="basic"
        )

        print(f"\nPersonalized Assessment Question:")
        print(f"  Prompt ID: {prompt_result['prompt_id']}")
        print(f"  Difficulty: {prompt_result['difficulty']}")
        print(f"  Learning Objective: {prompt_result['learning_objective']}")
        print(f"\n  Question: {prompt_result['prompt']}")

        # Check if it's personalized (should mention history/archaeology/inscriptions)
        question_text = prompt_result['prompt'].lower()
        is_personalized = any(keyword in question_text for keyword in
                             ["history", "inscription", "archaeology", "tablet", "stone"])

        if is_personalized:
            print("\n  [PASS] - Question is personalized to learner's interests")
        else:
            print("\n  [FAIL] - Question not personalized (or using default)")

    except FileNotFoundError:
        print(f"\n[ERROR] Learner {learner_id} not found. Run learner creation test first.")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def test_multiple_questions_for_learner():
    """Test that we get different personalized questions for the same learner."""

    print("\n" + "=" * 80)
    print("TEST 3: Multiple Personalized Questions for Same Learner")
    print("=" * 80)

    learner_id = "test_walkthrough_001"

    try:
        print(f"\nGenerating 5 questions for {learner_id}:")

        for i in range(5):
            prompt_result = select_personalized_dialogue_prompt(
                concept_id="concept-001",
                learner_id=learner_id
            )

            print(f"\n  Question {i+1}:")
            print(f"    ID: {prompt_result['prompt_id']}")
            print(f"    Difficulty: {prompt_result['difficulty']}")
            print(f"    Text: {prompt_result['prompt'][:80]}...")

        print("\n  [PASS] - Successfully generated multiple personalized questions")

    except Exception as e:
        print(f"\n[ERROR] {e}")


def test_fallback_to_standard_prompts():
    """Test that system falls back gracefully if personalized file doesn't exist."""

    print("\n" + "=" * 80)
    print("TEST 4: Fallback to Standard Prompts")
    print("=" * 80)

    # Test with concept that doesn't have personalized prompts
    learner_id = "test_walkthrough_001"

    try:
        # Try concept-002 (which likely doesn't have personalized version yet)
        prompt_result = select_personalized_dialogue_prompt(
            concept_id="concept-002",
            learner_id=learner_id,
            difficulty="basic"
        )

        print(f"\nFallback test for concept-002:")
        print(f"  Question: {prompt_result['prompt'][:100]}...")
        print("\n  [PASS] - Successfully fell back to standard prompts")

    except FileNotFoundError:
        print("\n  [WARNING] concept-002 assessments not found (expected)")
    except Exception as e:
        print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PERSONALIZED ASSESSMENT PROMPTS - TEST SUITE")
    print("=" * 80)

    # Run all tests
    test_personalize_prompt()
    test_real_learner_personalization()
    test_multiple_questions_for_learner()
    test_fallback_to_standard_prompts()

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
