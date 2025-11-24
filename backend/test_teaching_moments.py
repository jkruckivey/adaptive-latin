"""
Test script for personalized teaching moment assessments.

Teaching moments are two-stage misconception correction activities that
adapt scenarios to learner interests while maintaining pedagogical integrity.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.tools import select_personalized_teaching_moment, load_learner_model


def test_teaching_moment_personalization():
    """Test that teaching moments personalize correctly based on learner interests."""

    print("=" * 80)
    print("TEST 1: Teaching Moment Personalization")
    print("=" * 80)

    # Test with our history teacher learner
    learner_id = "test_walkthrough_001"

    try:
        learner_model = load_learner_model(learner_id)
        profile = learner_model.get("profile", {})

        print(f"\nLearner: {learner_id}")
        print(f"Interests: {profile.get('interests', 'N/A')}")

        # Get a teaching moment
        tm = select_personalized_teaching_moment(
            concept_id="concept-001",
            learner_id=learner_id
        )

        print(f"\nTeaching Moment: {tm['teaching_moment_id']}")
        print(f"Difficulty: {tm['difficulty']}")
        print(f"Learning Objective: {tm['learning_objective']}")

        print(f"\n--- SCENARIO ---")
        scenario = tm['scenario']
        print(f"Character: {scenario['character']}")
        print(f"Situation: {scenario['situation'][:100]}...")
        print(f"Misconception: \"{scenario['misconception'][:80]}...\"")

        # Check if personalized
        scenario_text = json.dumps(scenario).lower()
        is_personalized = any(kw in scenario_text for kw in
                             ["history", "inscription", "museum", "roman", "alex"])

        if is_personalized:
            print("\n[PASS] - Scenario personalized to history/archaeology interests")
        else:
            print("\n[FAIL] - Scenario not personalized")

        print(f"\n--- PART 1 ---")
        print(f"Prompt: {tm['part1']['prompt']}")
        print(f"Options: {len(tm['part1']['options'])} choices")

        print(f"\n--- PART 2 ---")
        print(f"Prompt: {tm['part2']['prompt']}")
        print(f"Pushbacks: {len(tm['part2']['pushbacks'])} variations")
        print(f"Options: {len(tm['part2']['options'])} choices")

        print(f"\n--- SCORING ---")
        for level in ["excellent", "good", "developing", "insufficient"]:
            if level in tm['scoring']:
                combos = tm['scoring'][level]['combinations']
                print(f"{level.capitalize()}: {len(combos)} combinations")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")


def test_different_learner_scenarios():
    """Test that different learners get different scenarios."""

    print("\n" + "=" * 80)
    print("TEST 2: Different Scenarios for Different Learners")
    print("=" * 80)

    test_learners = ["temp_history_learner", "temp_mythology_learner", "temp_literature_learner"]

    for learner_id in test_learners:
        try:
            learner_model = load_learner_model(learner_id)
            profile = learner_model.get("profile", {})

            tm = select_personalized_teaching_moment(
                concept_id="concept-001",
                learner_id=learner_id,
                difficulty="intermediate"
            )

            print(f"\n{learner_id}:")
            print(f"  Interests: {profile.get('interests', 'N/A')}")
            print(f"  Character: {tm['scenario']['character']}")
            print(f"  Situation hint: {tm['scenario']['situation'][:60]}...")

            # Identify scenario type
            scenario_text = json.dumps(tm['scenario']).lower()
            if 'history' in scenario_text or 'inscription' in scenario_text or 'alex' in scenario_text or 'morgan' in scenario_text:
                print(f"  Scenario: HISTORY")
            elif 'mythology' in scenario_text or 'gods' in scenario_text or 'jordan' in scenario_text or 'avery' in scenario_text:
                print(f"  Scenario: MYTHOLOGY")
            elif 'poetry' in scenario_text or 'catullus' in scenario_text or 'riley' in scenario_text or 'taylor' in scenario_text:
                print(f"  Scenario: LITERATURE")
            elif 'archaeology' in scenario_text or 'excavat' in scenario_text or 'sam' in scenario_text or 'casey' in scenario_text:
                print(f"  Scenario: ARCHAEOLOGY")
            else:
                print(f"  Scenario: DEFAULT")

        except FileNotFoundError:
            print(f"\n{learner_id}: Not found (create with test_question_variety.py)")
        except Exception as e:
            print(f"\n{learner_id}: Error - {e}")


def test_two_teaching_moments():
    """Test both teaching moments for concept-001."""

    print("\n" + "=" * 80)
    print("TEST 3: Both Teaching Moments Available")
    print("=" * 80)

    learner_id = "test_walkthrough_001"

    teaching_moment_ids = set()

    print(f"\nGetting 10 teaching moments for {learner_id}:")

    for i in range(10):
        try:
            tm = select_personalized_teaching_moment(
                concept_id="concept-001",
                learner_id=learner_id
            )

            teaching_moment_ids.add(tm['teaching_moment_id'])

            if i < 3:  # Show first 3
                print(f"\n{i+1}. {tm['teaching_moment_id']}")
                print(f"   Difficulty: {tm['difficulty']}")
                print(f"   Objective: {tm['learning_objective'][:60]}...")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            break

    print(f"\nUnique teaching moments found: {len(teaching_moment_ids)}")
    print(f"IDs: {teaching_moment_ids}")

    if len(teaching_moment_ids) >= 2:
        print("\n[PASS] - Multiple teaching moments available")
    else:
        print("\n[WARNING] - Only 1 teaching moment found")


def test_scoring_structure():
    """Test that scoring combinations are valid."""

    print("\n" + "=" * 80)
    print("TEST 4: Scoring Structure Validation")
    print("=" * 80)

    learner_id = "test_walkthrough_001"

    try:
        tm = select_personalized_teaching_moment(
            concept_id="concept-001",
            learner_id=learner_id
        )

        print(f"\nTeaching Moment: {tm['teaching_moment_id']}")

        # Get all part1 and part2 options
        part1_ids = [opt['id'] for opt in tm['part1']['options']]
        part2_ids = [opt['id'] for opt in tm['part2']['options']]

        print(f"\nPart 1 options: {part1_ids}")
        print(f"Part 2 options: {part2_ids}")

        # Check scoring combinations
        all_combinations = []
        for level in ["excellent", "good", "developing", "insufficient"]:
            if level in tm['scoring']:
                combos = tm['scoring'][level]['combinations']
                all_combinations.extend(combos)
                print(f"\n{level.capitalize()}: {combos}")

        print(f"\nTotal scored combinations: {len(all_combinations)}")

        # Verify combinations are valid
        invalid_combos = []
        for combo in all_combinations:
            # Handle wildcards
            if '*' in combo:
                continue

            # Check if both parts exist
            part1 = combo[0]
            part2 = combo[1]

            if part1 not in part1_ids:
                invalid_combos.append(f"{combo} - invalid part1: {part1}")
            if part2 not in part2_ids:
                invalid_combos.append(f"{combo} - invalid part2: {part2}")

        if invalid_combos:
            print(f"\n[FAIL] - Invalid combinations found:")
            for inv in invalid_combos:
                print(f"  {inv}")
        else:
            print(f"\n[PASS] - All combinations are valid")

    except Exception as e:
        print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEACHING MOMENT ASSESSMENTS - TEST SUITE")
    print("=" * 80)

    test_teaching_moment_personalization()
    test_different_learner_scenarios()
    test_two_teaching_moments()
    test_scoring_structure()

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
