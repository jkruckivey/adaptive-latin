"""
Configuration Management for Latin Adaptive Learning System

Loads environment variables and provides configuration settings for the application.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # API Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # CORS Settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # File Paths (works on both Windows and Linux)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    RESOURCE_BANK_DIR: Path = BASE_DIR.parent / "resource-bank" / "latin-grammar"

    # Learner models directory - use persistent disk path in production if set
    LEARNER_MODELS_DIR: Path = Path(os.getenv("LEARNER_MODELS_PATH", str(BASE_DIR / "data" / "learner-models")))

    PROMPTS_DIR: Path = BASE_DIR / "prompts"

    # System Prompts (now located in backend/prompts/ for better organization)
    SYSTEM_PROMPT_FILE: Path = PROMPTS_DIR / "tutor-agent-system-prompt-active.md"
    CONFIDENCE_PROMPT_FILE: Path = PROMPTS_DIR / "confidence-response-addendum.md"
    CONTENT_GENERATION_PROMPT_FILE: Path = PROMPTS_DIR / "content-generation-addendum.md"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Mastery Thresholds
    MASTERY_THRESHOLD: float = float(os.getenv("MASTERY_THRESHOLD", "0.85"))
    CONTINUE_THRESHOLD: float = float(os.getenv("CONTINUE_THRESHOLD", "0.70"))

    # Assessment Settings
    MIN_ASSESSMENTS_FOR_MASTERY: int = int(os.getenv("MIN_ASSESSMENTS_FOR_MASTERY", "3"))
    MASTERY_WINDOW_SIZE: int = int(os.getenv("MASTERY_WINDOW_SIZE", "10"))

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        errors = []

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required")

        if not cls.RESOURCE_BANK_DIR.exists():
            errors.append(f"Resource bank directory not found: {cls.RESOURCE_BANK_DIR}")

        if not cls.SYSTEM_PROMPT_FILE.exists():
            errors.append(f"System prompt file not found: {cls.SYSTEM_PROMPT_FILE}")

        if not cls.CONFIDENCE_PROMPT_FILE.exists():
            errors.append(f"Confidence prompt file not found: {cls.CONFIDENCE_PROMPT_FILE}")

        if not cls.CONTENT_GENERATION_PROMPT_FILE.exists():
            errors.append(f"Content generation prompt file not found: {cls.CONTENT_GENERATION_PROMPT_FILE}")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.LEARNER_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_concept_dir(cls, concept_id: str) -> Path:
        """Get the directory path for a specific concept."""
        return cls.RESOURCE_BANK_DIR / concept_id

    @classmethod
    def get_learner_file(cls, learner_id: str) -> Path:
        """Get the file path for a learner's model."""
        return cls.LEARNER_MODELS_DIR / f"{learner_id}.json"


# Singleton instance
config = Config()
