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

    # Course Settings
    DEFAULT_COURSE_ID: str = os.getenv("DEFAULT_COURSE_ID", "latin-grammar")

    # File Paths (works on both Windows and Linux)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    RESOURCE_BANK_DIR: Path = BASE_DIR.parent / "resource-bank"
    USER_COURSES_DIR: Path = RESOURCE_BANK_DIR / "user-courses"

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
        cls.USER_COURSES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_course_dir(cls, course_id: str) -> Path:
        """Get the directory path for a specific course."""
        # Check if it's a user-created course
        user_course_path = cls.USER_COURSES_DIR / course_id
        if user_course_path.exists():
            return user_course_path

        # Otherwise, check built-in courses in resource bank
        builtin_course_path = cls.RESOURCE_BANK_DIR / course_id
        if builtin_course_path.exists():
            return builtin_course_path

        # Default to built-in path (for new course creation)
        return builtin_course_path

    @classmethod
    def get_concept_dir(cls, concept_id: str, course_id: Optional[str] = None) -> Path:
        """Get the directory path for a specific concept within a course."""
        if course_id is None:
            course_id = cls.DEFAULT_COURSE_ID

        course_dir = cls.get_course_dir(course_id)
        return course_dir / concept_id

    @classmethod
    def get_learner_file(cls, learner_id: str) -> Path:
        """Get the file path for a learner's model."""
        return cls.LEARNER_MODELS_DIR / f"{learner_id}.json"

# Singleton instance
config = Config()

# Database
config.DATABASE_FILE = config.LEARNER_MODELS_DIR.parent / "latin_learner.db"

# Security
config.SECRET_KEY = os.environ.get("SECRET_KEY", "a_super_secret_key")
config.ALGORITHM = "HS256"
config.ACCESS_TOKEN_EXPIRE_MINUTES = 30
