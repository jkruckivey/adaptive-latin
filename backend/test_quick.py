#!/usr/bin/env python3
"""
Quick smoke test to verify the refactored code works.
Run with: python test_quick.py
"""

import sys
sys.path.insert(0, '/home/user/adaptive-latin/backend')

print("=" * 60)
print("QUICK SMOKE TEST - Testing Refactored Code")
print("=" * 60)

# Test 1: Import constants
print("\n1. Testing constants.py...")
try:
    from app.constants import (
        PREVIEW_READ_TIME_SECONDS,
        STAGE_PREVIEW,
        STAGE_START,
        VALID_LEARNING_STYLES
    )
    print(f"   ✓ Constants imported successfully")
    print(f"   ✓ PREVIEW_READ_TIME_SECONDS = {PREVIEW_READ_TIME_SECONDS}")
    print(f"   ✓ STAGE_PREVIEW = '{STAGE_PREVIEW}'")
    print(f"   ✓ VALID_LEARNING_STYLES = {VALID_LEARNING_STYLES}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Import and test sanitize_user_input
print("\n2. Testing content_generators.py - sanitize_user_input()...")
try:
    from app.content_generators import sanitize_user_input

    # Test normal input
    result1 = sanitize_user_input("Hello world")
    assert result1 == "Hello world", "Normal input failed"
    print(f"   ✓ Normal input works: '{result1}'")

    # Test code fence injection
    result2 = sanitize_user_input("```python\nmalicious()\n```")
    assert "```" not in result2, "Code fence escaping failed"
    print(f"   ✓ Code fence escaped: {result2[:50]}")

    # Test length limit
    result3 = sanitize_user_input("A" * 2000, max_length=100)
    assert len(result3) == 100, "Length limiting failed"
    print(f"   ✓ Length limit works: {len(result3)} chars")

    print(f"   ✓ sanitize_user_input() works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import and test request generators
print("\n3. Testing content_generators.py - request generators...")
try:
    from app.content_generators import (
        generate_preview_request,
        generate_diagnostic_request,
        generate_practice_request
    )

    # Test preview request
    preview_req = generate_preview_request('narrative')
    assert 'example-set' in preview_req, "Preview request failed"
    print(f"   ✓ generate_preview_request() works")
    print(f"      Sample: {preview_req[:80]}...")

    # Test diagnostic request
    diag_req = generate_diagnostic_request(is_cumulative=False)
    assert 'multiple-choice' in diag_req, "Diagnostic request failed"
    print(f"   ✓ generate_diagnostic_request() works")

    # Test practice request
    practice_req = generate_practice_request(is_cumulative=False)
    assert 'multiple-choice' in practice_req, "Practice request failed"
    print(f"   ✓ generate_practice_request() works")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Verify agent.py imports the new modules
print("\n4. Testing agent.py integration...")
try:
    # Just check that the file is syntactically correct
    import ast
    with open('/home/user/adaptive-latin/backend/app/agent.py', 'r') as f:
        code = f.read()
        ast.parse(code)
    print(f"   ✓ agent.py syntax is valid")

    # Check that it imports from the new modules
    assert 'from .constants import' in code, "Missing constants import"
    assert 'from .content_generators import' in code, "Missing content_generators import"
    print(f"   ✓ agent.py imports from new modules")

    # Check that old code is removed
    assert 'def sanitize_user_input' not in code or '# sanitize_user_input has been moved' in code, "Old sanitize_user_input still exists"
    print(f"   ✓ Duplicate code removed")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL SMOKE TESTS PASSED!")
print("=" * 60)
print("\nThe refactoring is complete and working. To run full tests:")
print("  1. Install dependencies: pip install -r requirements.txt")
print("  2. Run tests: pytest tests/ -v")
print("=" * 60)
