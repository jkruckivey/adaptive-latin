"""
Tests for content generation request builders

These tests ensure that the extracted content generation functions
produce the correct prompts for different scenarios.
"""

import pytest
from app.content_generators import (
    generate_preview_request,
    generate_diagnostic_request,
    generate_practice_request,
    build_question_context_string
)


class TestPreviewGeneration:
    """Tests for preview content request generation."""

    def test_narrative_preview(self):
        """Test preview request for narrative learning style."""
        request = generate_preview_request('narrative')
        assert 'example-set' in request
        assert '30-second read' in request or 'brief' in request
        assert 'preview' in request.lower()

    def test_varied_preview(self):
        """Test preview request for varied learning style."""
        # Run multiple times to test randomness
        requests = [generate_preview_request('varied') for _ in range(5)]
        # Should see variety in the content types
        all_requests = ' '.join(requests)
        # At least one should be generated (randomness may not hit all types in 5 tries)
        assert any(ct in all_requests for ct in ['paradigm-table', 'example-set', 'lesson', 'declension-explorer'])

    def test_adaptive_preview(self):
        """Test preview request for adaptive learning style."""
        request = generate_preview_request('adaptive')
        assert 'lesson' in request
        assert '30-second' in request or 'brief' in request

    def test_default_preview(self):
        """Test preview request for unknown learning style."""
        request = generate_preview_request('unknown-style')
        assert 'lesson' in request
        assert 'preview' in request.lower()


class TestDiagnosticGeneration:
    """Tests for diagnostic question request generation."""

    def test_regular_diagnostic(self):
        """Test regular (non-cumulative) diagnostic request."""
        request = generate_diagnostic_request(is_cumulative=False)
        assert 'multiple-choice' in request
        assert 'diagnostic' in request.lower()
        assert 'Roman context' in request or 'inscription' in request

    def test_cumulative_diagnostic(self):
        """Test cumulative review diagnostic request."""
        cumulative_concepts = ['concept-001', 'concept-002', 'concept-003']
        request = generate_diagnostic_request(is_cumulative=True, cumulative_concepts=cumulative_concepts)
        assert 'CUMULATIVE' in request
        assert 'integrates' in request.lower()
        assert 'is_cumulative: true' in request


class TestPracticeGeneration:
    """Tests for practice question request generation."""

    def test_regular_practice(self):
        """Test regular practice question request."""
        request = generate_practice_request(is_cumulative=False)
        assert 'multiple-choice' in request
        assert 'DIFFERENT scenario' in request or 'vary' in request.lower()

    def test_cumulative_practice(self):
        """Test cumulative practice question request."""
        cumulative_concepts = ['concept-001', 'concept-002']
        request = generate_practice_request(is_cumulative=True, cumulative_concepts=cumulative_concepts)
        assert 'CUMULATIVE' in request
        assert 'is_cumulative: true' in request


class TestQuestionContextBuilder:
    """Tests for question context string builder."""

    def test_builds_context_string(self):
        """Test that question context is properly formatted."""
        question_context = {
            'scenario': 'You see an inscription on a temple',
            'question': 'What case is used?',
            'user_answer': 0,
            'correct_answer': 1,
            'options': ['Nominative', 'Genitive', 'Accusative']
        }
        result = build_question_context_string(question_context)

        assert 'QUESTION THEY JUST ANSWERED INCORRECTLY' in result
        assert 'You see an inscription on a temple' in result
        assert 'What case is used?' in result
        assert 'Nominative' in result
        assert 'Genitive' in result
        assert '✓ CORRECT' in result
        assert '✗ THEY CHOSE THIS' in result

    def test_handles_none_context(self):
        """Test handling of None context."""
        result = build_question_context_string(None)
        assert result == ""

    def test_handles_empty_context(self):
        """Test handling of empty context."""
        result = build_question_context_string({})
        assert "scenario" in result.lower() or result == ""

    def test_sanitizes_input(self):
        """Test that malicious input in context is sanitized."""
        question_context = {
            'scenario': '```python\nmalicious()\n```',
            'question': 'Test?',
            'user_answer': 0,
            'correct_answer': 1,
            'options': ['A', 'B']
        }
        result = build_question_context_string(question_context)
        # Should not contain raw code fences
        assert '```python' not in result
