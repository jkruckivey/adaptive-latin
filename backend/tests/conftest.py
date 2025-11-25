"""
Pytest configuration and shared fixtures

Add any shared test fixtures here.
"""

import pytest
import sys
from pathlib import Path

# Add the backend directory to the path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def sample_learner_profile():
    """Fixture providing a sample learner profile for testing."""
    return {
        "learningStyle": "narrative",
        "priorKnowledge": {
            "languageDetails": "Spanish - 3 years, some German"
        },
        "grammarExperience": "okay",
        "interests": "Roman history, mythology, architecture"
    }


@pytest.fixture
def sample_multiple_choice():
    """Fixture providing a valid multiple-choice question."""
    return {
        "type": "multiple-choice",
        "scenario": "You see the inscription 'SPQR' on a Roman standard",
        "question": "What case is 'Senatus' in SPQR?",
        "options": ["Nominative", "Genitive", "Accusative", "Dative"],
        "correctAnswer": 1
    }


@pytest.fixture
def sample_fill_blank():
    """Fixture providing a valid fill-blank exercise."""
    return {
        "type": "fill-blank",
        "sentence": "Puella rosam {blank} dat.",
        "blanks": ["magistrae"],
        "correctAnswers": ["magistrae"]
    }
