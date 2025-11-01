"""
Tests for content validation functions

These tests ensure that AI-generated content is validated correctly
before being sent to learners.
"""

import pytest
from app.agent import validate_diagnostic_content


class TestMultipleChoiceValidation:
    """Tests for multiple-choice question validation."""

    def test_valid_multiple_choice(self):
        """Test that a properly formatted multiple-choice question validates."""
        content = {
            "type": "multiple-choice",
            "correctAnswer": 1,
            "options": ["Roma", "Romae", "Romam"],
            "scenario": "You see an inscription on a Roman building",
            "question": "What case is 'Romae' in this inscription?"
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == True
        assert error == ""

    def test_invalid_answer_index(self):
        """Test that out-of-bounds answer index is caught."""
        content = {
            "type": "multiple-choice",
            "correctAnswer": 5,  # Out of bounds!
            "options": ["A", "B", "C"],
            "scenario": "Test scenario",
            "question": "Test question?"
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "out of bounds" in error

    def test_duplicate_options(self):
        """Test that duplicate answer options are caught."""
        content = {
            "type": "multiple-choice",
            "correctAnswer": 1,
            "options": ["Roma", "Roma", "Romam"],  # Duplicate!
            "scenario": "Test scenario",
            "question": "Test question?"
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "duplicate" in error.lower()

    def test_missing_scenario(self):
        """Test that missing scenario is caught."""
        content = {
            "type": "multiple-choice",
            "correctAnswer": 1,
            "options": ["A", "B", "C"],
            "question": "Test question?"
            # Missing scenario
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "scenario" in error.lower()

    def test_missing_correct_answer(self):
        """Test that missing correctAnswer is caught."""
        content = {
            "type": "multiple-choice",
            "options": ["A", "B", "C"],
            "scenario": "Test",
            "question": "Test?"
            # Missing correctAnswer
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "correctAnswer" in error


class TestFillBlankValidation:
    """Tests for fill-blank exercise validation."""

    def test_valid_fill_blank(self):
        """Test that a properly formatted fill-blank exercise validates."""
        content = {
            "type": "fill-blank",
            "sentence": "The girl gives the rose to {blank}",
            "blanks": ["puellae"],
            "correctAnswers": ["puellae"]
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == True
        assert error == ""

    def test_mismatched_blanks_and_answers(self):
        """Test that mismatched blank count is caught."""
        content = {
            "type": "fill-blank",
            "sentence": "The girl gives {blank} to {blank}",
            "blanks": ["rosa", "puellae"],
            "correctAnswers": ["rosam"]  # Only 1 answer for 2 blanks!
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "blanks" in error.lower() and "correctAnswers" in error


class TestDialogueValidation:
    """Tests for dialogue question validation."""

    def test_valid_dialogue(self):
        """Test that a dialogue question with a question validates."""
        content = {
            "type": "dialogue",
            "question": "Explain the difference between nominative and accusative case."
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == True
        assert error == ""

    def test_missing_question(self):
        """Test that dialogue without a question is caught."""
        content = {
            "type": "dialogue"
            # Missing question
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == False
        assert "question" in error.lower()


class TestNonDiagnosticContent:
    """Tests for non-diagnostic content types (lessons, examples, etc.)."""

    def test_lesson_content_passes(self):
        """Test that lesson content doesn't trigger validation errors."""
        content = {
            "type": "lesson",
            "title": "First Declension",
            "content": "Latin nouns ending in -a are typically first declension..."
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == True
        assert error == ""

    def test_example_set_passes(self):
        """Test that example-set content doesn't trigger validation errors."""
        content = {
            "type": "example-set",
            "examples": [
                {"latin": "puella", "translation": "girl"},
                {"latin": "rosa", "translation": "rose"}
            ]
        }
        is_valid, error = validate_diagnostic_content(content)
        assert is_valid == True
        assert error == ""
