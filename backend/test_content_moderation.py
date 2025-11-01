#!/usr/bin/env python3
"""
Test script for content moderation functionality.
Tests that inappropriate interests are properly blocked.
"""

import sys
sys.path.insert(0, '.')

from app.content_generators import moderate_user_interests


def test_moderation():
    """Test content moderation with various inputs."""

    test_cases = [
        # (input, should_pass, description)
        ("astronomy, history, art", True, "Safe interests"),
        ("cooking, travel, music", True, "Safe interests"),
        ("eating babies", False, "Explicit disturbing content"),
        ("killing people", False, "Violence"),
        ("porn videos", False, "Sexual content"),
        ("cocaine and drugs", False, "Drug content"),
        ("nazi ideology", False, "Hate speech"),
        ("I love to fuck", False, "Profanity"),
        ("Roman history, Latin poetry", True, "Academic interests"),
        ("astronomy, death metal music", False, "Contains 'death'"),
        ("medieval weapons", False, "Contains 'weapon'"),
        ("gardening, cooking", True, "Wholesome interests"),
    ]

    print("=" * 70)
    print("CONTENT MODERATION TESTS")
    print("=" * 70)

    passed = 0
    failed = 0

    for interests, should_pass, description in test_cases:
        result = moderate_user_interests(interests)
        is_safe = result["is_safe"]

        # Check if result matches expectation
        if is_safe == should_pass:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"\n{status}: {description}")
        print(f"   Input: '{interests}'")
        print(f"   Expected: {'SAFE' if should_pass else 'BLOCKED'}")
        print(f"   Got: {'SAFE' if is_safe else 'BLOCKED'}")

        if not is_safe:
            print(f"   Reason: {result['reason']}")

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_moderation()
    sys.exit(0 if success else 1)
