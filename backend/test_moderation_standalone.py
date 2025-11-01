#!/usr/bin/env python3
"""
Standalone test for content moderation (no dependencies).
Copy of the moderate_user_interests function for testing.
"""

# Blocklist (copy from content_generators.py)
INAPPROPRIATE_TERMS = [
    # Violence
    "kill", "murder", "death", "blood", "gore", "torture", "weapon", "gun", "knife",
    "stab", "shoot", "harm", "hurt", "attack", "assault",
    # Sexual content
    "sex", "porn", "naked", "nude", "erotic", "sexual", "rape", "molest", "abuse",
    # Drugs
    "drug", "cocaine", "heroin", "meth", "marijuana", "cannabis",
    # Concerning combinations with children (matches plurals)
    "eat bab", "eating bab", "kill bab", "hurt bab", "dead bab",  # Catches baby/babies
    "eat child", "eating child", "kill child", "hurt child", "dead child",
    "eat infant", "eating infant", "kill infant",
    # Hate speech
    "nazi", "genocide", "supremacist",
    # Profanity
    "fuck", "shit", "bitch", "damn", "bastard",
    "piss", "cock", "dick", "pussy", "whore", "slut"
]


def moderate_user_interests(interests: str):
    """Content moderation function (standalone copy)."""
    if not interests or not isinstance(interests, str):
        return {"is_safe": True, "sanitized": "", "reason": None}

    interests_lower = interests.lower().strip()

    # Check against blocklist
    for term in INAPPROPRIATE_TERMS:
        if term in interests_lower:
            return {
                "is_safe": False,
                "sanitized": "",
                "reason": f"Inappropriate content detected. Please use appropriate topics."
            }

    # Basic sanitization
    sanitized = interests[:500]
    sanitized = ' '.join(sanitized.split())

    return {"is_safe": True, "sanitized": sanitized, "reason": None}


# Test cases
test_cases = [
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
