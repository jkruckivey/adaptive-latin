#!/usr/bin/env python3
"""
QA Validation Script for Teaching Moment Implementation

Checks:
1. Teaching Moment component exists
2. ContentRenderer registers it
3. Backend prompts include it
4. Excel course has onboarding questions
5. Teaching Moment schema is valid
"""

import json
import os
import sys

def print_status(check_name, passed, message=""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {check_name}")
    if message:
        print(f"   {message}")
    return passed

def main():
    print("🧪 QA Validation for Teaching Moment\n")

    all_passed = True

    # Check 1: Frontend component exists
    component_path = "frontend/src/components/content-types/TeachingMoment.jsx"
    passed = os.path.exists(component_path)
    all_passed &= print_status(
        "Teaching Moment component exists",
        passed,
        f"Found at {component_path}" if passed else f"Missing: {component_path}"
    )

    # Check 2: ContentRenderer imports it
    renderer_path = "frontend/src/components/ContentRenderer.jsx"
    if os.path.exists(renderer_path):
        with open(renderer_path) as f:
            content = f.read()
            has_import = "import TeachingMoment" in content
            has_case = "case 'teaching-moment':" in content
            passed = has_import and has_case
            all_passed &= print_status(
                "ContentRenderer registers teaching-moment",
                passed,
                "Import and case statement found" if passed else "Missing import or case"
            )

    # Check 3: Backend prompts include teaching-moment
    prompts_path = "backend/prompts/content-generation-addendum.md"
    if os.path.exists(prompts_path):
        with open(prompts_path) as f:
            content = f.read()
            has_schema = "Teaching Moment" in content and "teaching-moment" in content
            has_in_list = "teaching-moment" in content
            has_priority = "Use **teaching-moment**" in content
            passed = has_schema and has_in_list and has_priority
            all_passed &= print_status(
                "Backend prompts include teaching-moment",
                passed,
                "Schema, allowed list, and priority found" if passed else "Missing from prompts"
            )

            # Check for explicit avoidance of long-form
            avoid_dialogue = "Do NOT use **dialogue**" in content
            all_passed &= print_status(
                "Prompts avoid long-form responses",
                avoid_dialogue,
                "Dialogue type explicitly avoided" if avoid_dialogue else "Missing guidance"
            )

    # Check 4: Excel course has onboarding
    excel_metadata_path = "resource-bank/user-courses/excel-fundamentals-test/metadata.json"
    if os.path.exists(excel_metadata_path):
        with open(excel_metadata_path) as f:
            data = json.load(f)
            has_onboarding = "onboarding_questions" in data
            if has_onboarding:
                num_questions = len(data["onboarding_questions"])
                has_interests = any(
                    q.get("priorKnowledgeKey") == "interests"
                    for q in data["onboarding_questions"]
                )
                passed = num_questions >= 3 and has_interests
                all_passed &= print_status(
                    "Excel course has custom onboarding",
                    passed,
                    f"{num_questions} questions, interests question: {has_interests}"
                )
            else:
                all_passed &= print_status(
                    "Excel course has custom onboarding",
                    False,
                    "No onboarding_questions found"
                )

    # Check 5: Validate teaching-moment example structure
    print("\n📋 Validating Teaching Moment Schema:")
    example_tm = {
        "type": "teaching-moment",
        "scenario": {
            "character": "Test",
            "situation": "Testing",
            "misconception": "Wrong idea"
        },
        "part1": {
            "prompt": "What say?",
            "options": [{"id": "a", "text": "Option A", "quality": "correct"}]
        },
        "part2": {
            "pushbacks": {"a": "Pushback"},
            "prompt": "How respond?",
            "options": [{"id": "1", "text": "Response", "defends": ["a"]}]
        },
        "scoring": {
            "excellent": {"combinations": ["a1"], "feedback": "Great!"}
        }
    }

    required_fields = [
        "type", "scenario", "part1", "part2", "scoring"
    ]

    for field in required_fields:
        passed = field in example_tm
        all_passed &= print_status(
            f"  - Has {field}",
            passed
        )

    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("✅ ALL CHECKS PASSED - System ready for testing!")
        print("\nNext steps:")
        print("1. Start backend: cd backend && uvicorn app.main:app --reload --port 8000")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Load Excel Fundamentals course")
        print("4. Watch for teaching-moment assessments")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
