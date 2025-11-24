"""
Diagnostic script to verify question variety in personalized assessments.

This script checks that:
1. Different base questions are being selected
2. Personalization is consistent for same learner
3. Different learners get different scenarios for SAME questions
"""

import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from app.tools import (
    select_personalized_dialogue_prompt,
    load_learner_model,
    create_learner_model
)


def test_question_variety():
    """Verify we get different base questions."""

    print("=" * 80)
    print("TEST 1: Question Variety - Same Learner, Multiple Questions")
    print("=" * 80)

    learner_id = "test_walkthrough_001"
    num_samples = 20

    prompt_ids = []
    difficulties = []
    learning_objectives = []

    print(f"\nGenerating {num_samples} questions for {learner_id}:")
    print("-" * 80)

    for i in range(num_samples):
        result = select_personalized_dialogue_prompt(
            concept_id="concept-001",
            learner_id=learner_id
        )

        prompt_ids.append(result['prompt_id'])
        difficulties.append(result['difficulty'])
        learning_objectives.append(result['learning_objective'])

        if i < 5:  # Show first 5
            print(f"\n{i+1}. ID: {result['prompt_id']}")
            print(f"   Difficulty: {result['difficulty']}")
            print(f"   Objective: {result['learning_objective'][:60]}...")
            print(f"   Question: {result['prompt'][:80]}...")

    # Analyze variety
    print("\n" + "=" * 80)
    print("VARIETY ANALYSIS:")
    print("=" * 80)

    print(f"\nPrompt ID Distribution:")
    id_counts = Counter(prompt_ids)
    for prompt_id, count in sorted(id_counts.items()):
        percentage = (count / num_samples) * 100
        print(f"  {prompt_id}: {count} times ({percentage:.1f}%)")

    print(f"\nDifficulty Distribution:")
    diff_counts = Counter(difficulties)
    for difficulty, count in sorted(diff_counts.items()):
        percentage = (count / num_samples) * 100
        print(f"  {difficulty}: {count} times ({percentage:.1f}%)")

    print(f"\nUnique base questions: {len(id_counts)}")
    print(f"Unique learning objectives: {len(set(learning_objectives))}")

    if len(id_counts) >= 5:
        print("\n[PASS] - Good variety in base questions")
    else:
        print("\n[FAIL] - Limited variety in base questions")


def test_same_question_different_learners():
    """Verify different learners get different scenarios for same base question."""

    print("\n" + "=" * 80)
    print("TEST 2: Same Question, Different Learner Scenarios")
    print("=" * 80)

    # Create temporary test learners with different interests
    test_learners = [
        {
            "id": "temp_history_learner",
            "profile": {"interests": "Roman history, inscriptions"}
        },
        {
            "id": "temp_mythology_learner",
            "profile": {"interests": "mythology, gods and goddesses"}
        },
        {
            "id": "temp_literature_learner",
            "profile": {"interests": "literature, poetry"}
        }
    ]

    print("\nCreating temporary test learners...")

    for learner in test_learners:
        try:
            create_learner_model(
                learner_id=learner['id'],
                profile=learner['profile'],
                course_id="latin-grammar"
            )
            print(f"  Created: {learner['id']}")
        except ValueError:
            print(f"  Already exists: {learner['id']}")

    # Get dialogue-001-1 (basic first declension identification) for each learner
    print("\n" + "-" * 80)
    print("Getting 'dialogue-001-1' for each learner:")
    print("-" * 80)

    for learner in test_learners:
        # Keep requesting until we get dialogue-001-1
        for attempt in range(20):
            result = select_personalized_dialogue_prompt(
                concept_id="concept-001",
                learner_id=learner['id'],
                difficulty="basic"
            )

            if result['prompt_id'] == 'dialogue-001-1':
                print(f"\n{learner['id']}:")
                print(f"  Interests: {learner['profile']['interests']}")
                print(f"  Question: {result['prompt'][:100]}...")

                # Check which scenario keywords appear
                question_lower = result['prompt'].lower()
                if 'inscription' in question_lower or 'memoriae' in question_lower:
                    print(f"  Scenario: HISTORY")
                elif 'gods' in question_lower or 'goddess' in question_lower or 'fortunae' in question_lower:
                    print(f"  Scenario: MYTHOLOGY")
                elif 'poem' in question_lower or 'rosa' in question_lower:
                    print(f"  Scenario: LITERATURE")
                else:
                    print(f"  Scenario: DEFAULT or OTHER")
                break

    print("\n[INFO] - Check that each learner received a different scenario")


def test_personalization_consistency():
    """Verify same learner gets same scenario for same question."""

    print("\n" + "=" * 80)
    print("TEST 3: Personalization Consistency")
    print("=" * 80)

    learner_id = "test_walkthrough_001"

    print(f"\nGetting dialogue-001-1 five times for {learner_id}:")
    print("-" * 80)

    scenarios = []

    for i in range(5):
        # Keep requesting until we get dialogue-001-1
        for attempt in range(20):
            result = select_personalized_dialogue_prompt(
                concept_id="concept-001",
                learner_id=learner_id,
                difficulty="basic"
            )

            if result['prompt_id'] == 'dialogue-001-1':
                scenarios.append(result['prompt'])
                print(f"\n{i+1}. {result['prompt'][:80]}...")
                break

    # Check consistency
    if len(set(scenarios)) == 1:
        print("\n[PASS] - Same question always gets same scenario for same learner")
    else:
        print("\n[FAIL] - Inconsistent scenarios for same question/learner")
        print(f"Got {len(set(scenarios))} different versions")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("QUESTION VARIETY DIAGNOSTIC")
    print("=" * 80)

    test_question_variety()
    test_same_question_different_learners()
    test_personalization_consistency()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
