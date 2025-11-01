"""
Application Constants

Centralized constants for the Latin Adaptive Learning System.
Using named constants improves readability and maintainability.
"""

# ============================================================================
# Content Generation Settings
# ============================================================================

# Preview content
PREVIEW_READ_TIME_SECONDS = 30
PREVIEW_CONTENT_TYPES = ['paradigm-table', 'example-set', 'lesson', 'declension-explorer']

# Cumulative review
CUMULATIVE_REVIEW_CONCEPTS_COUNT = 3
MIN_CONCEPTS_FOR_CUMULATIVE = 2

# Question history
RECENT_QUESTIONS_DISPLAY_COUNT = 5
MAX_QUESTIONS_IN_HISTORY = 10

# ============================================================================
# API Rate Limits
# ============================================================================

REQUEST_SIZE_LIMIT_BYTES = 1024 * 1024  # 1 MB
REQUEST_SIZE_LIMIT_MB = 1

# Rate limit strings (for slowapi decorator)
LEARNER_CREATION_RATE_LIMIT = "10/minute"
CHAT_RATE_LIMIT = "30/minute"
CONTENT_GENERATION_RATE_LIMIT = "60/minute"
SUBMIT_RESPONSE_RATE_LIMIT = "60/minute"

# ============================================================================
# API Retry Settings
# ============================================================================

DEFAULT_MAX_RETRIES = 3
DEFAULT_API_TIMEOUT_SECONDS = 30
RETRY_BACKOFF_BASE = 2  # Exponential backoff: 2^attempt seconds

# ============================================================================
# Mastery & Assessment
# ============================================================================

DEFAULT_MASTERY_THRESHOLD = 0.85
DEFAULT_CONTINUE_THRESHOLD = 0.70
MIN_ASSESSMENTS_FOR_MASTERY = 3
DEFAULT_MASTERY_WINDOW_SIZE = 10

# Confidence ratings
MIN_CONFIDENCE_LEVEL = 1
MAX_CONFIDENCE_LEVEL = 4
HIGH_CONFIDENCE_THRESHOLD = 3  # 3+ stars = high confidence

# ============================================================================
# Content Types
# ============================================================================

VALID_RESOURCE_TYPES = ["text-explainer", "examples"]
VALID_ASSESSMENT_TYPES = ["dialogue", "written", "applied"]
VALID_QUESTION_TYPES = ["multiple-choice", "fill-blank", "dialogue"]

# Content type classifications
DIAGNOSTIC_CONTENT_TYPES = ["multiple-choice", "fill-blank", "dialogue"]
INSTRUCTIONAL_CONTENT_TYPES = ["lesson", "example-set", "paradigm-table"]
INTERACTIVE_WIDGET_TYPES = ["declension-explorer", "word-order-manipulator"]

# ============================================================================
# Learning Styles
# ============================================================================

VALID_LEARNING_STYLES = ["narrative", "varied", "adaptive"]

# Content preferences by learning style
NARRATIVE_CONTENT_TYPES = ["example-set", "lesson"]
VARIED_CONTENT_TYPES = ["paradigm-table", "example-set", "lesson", "declension-explorer", "word-order-manipulator"]
ADAPTIVE_CONTENT_TYPES = ["lesson", "fill-blank", "multiple-choice"]

# ============================================================================
# Remediation Types
# ============================================================================

REMEDIATION_TYPE_BRIEF = "brief"
REMEDIATION_TYPE_SUPPORTIVE = "supportive"
REMEDIATION_TYPE_FULL_CALIBRATION = "full_calibration"

# ============================================================================
# Learning Stages
# ============================================================================

STAGE_PREVIEW = "preview"
STAGE_START = "start"
STAGE_PRACTICE = "practice"
STAGE_ASSESS = "assess"
STAGE_REMEDIATE = "remediate"
STAGE_REINFORCE = "reinforce"

# ============================================================================
# Input Validation
# ============================================================================

MAX_USER_INPUT_LENGTH = 1000
MAX_SPECIAL_CHAR_REPETITION = 3  # Max consecutive special characters

# Prompt injection patterns to escape
INJECTION_PATTERNS = {
    'code_fence': '```',
    'markdown_header': '###',
    'xml_tag_open': '<|',
    'xml_tag_close': '>|',
    'instruction_open': '[INST]',
    'instruction_close': '[/INST]'
}

# ============================================================================
# HTTP Status Codes (for clarity)
# ============================================================================

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_PAYLOAD_TOO_LARGE = 413
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_INTERNAL_SERVER_ERROR = 500

# ============================================================================
# Calibration Types
# ============================================================================

CALIBRATION_CALIBRATED = "calibrated"
CALIBRATION_UNDERCONFIDENT = "underconfident"
CALIBRATION_OVERCONFIDENT = "overconfident"
CALIBRATION_CALIBRATED_LOW = "calibrated_low"

# ============================================================================
# Spaced Repetition
# ============================================================================

# Default review intervals (in days)
REVIEW_INTERVAL_INITIAL = 1
REVIEW_INTERVAL_EASY = 7
REVIEW_INTERVAL_MEDIUM = 3
REVIEW_INTERVAL_HARD = 1

# ============================================================================
# External Resources
# ============================================================================

MAX_EXTERNAL_RESOURCES_TO_ATTACH = 2

# Requirement levels
REQUIREMENT_LEVEL_OPTIONAL = "optional"
REQUIREMENT_LEVEL_RECOMMENDED = "recommended"
REQUIREMENT_LEVEL_REQUIRED = "required"

# Verification methods
VERIFICATION_METHOD_NONE = "none"
VERIFICATION_METHOD_SELF_ATTESTATION = "self-attestation"
VERIFICATION_METHOD_COMPREHENSION_QUIZ = "comprehension-quiz"
VERIFICATION_METHOD_DISCUSSION_PROMPT = "discussion-prompt"

# ============================================================================
# Adaptive Scaffolding & Difficulty
# ============================================================================

# Difficulty levels
DIFFICULTY_EASIER = "easier"
DIFFICULTY_APPROPRIATE = "appropriate"
DIFFICULTY_HARDER = "harder"

# Performance thresholds for difficulty adjustment
DIFFICULTY_DOWN_THRESHOLD = 0.40  # Below 40% recent performance -> easier questions
DIFFICULTY_UP_THRESHOLD = 0.85    # Above 85% recent performance -> harder questions

# Sliding window for recent performance calculation
DIFFICULTY_ASSESSMENT_WINDOW = 5  # Look at last 5 questions

# Adaptive mastery thresholds (lower when struggling)
MASTERY_THRESHOLD_STRUGGLING = 0.70  # When recent performance < 40%
MASTERY_THRESHOLD_NORMAL = 0.75      # Default (lowered from 0.85)
MASTERY_THRESHOLD_EXCELLING = 0.85   # When recent performance > 85%

# ============================================================================
# Choice & Agency (Practice Mode)
# ============================================================================

# Practice mode settings
PRACTICE_MODE_ENABLED = True
PRACTICE_MODE_DEFAULT = False  # Learners start in graded mode by default

# Practice mode features
PRACTICE_MODE_SHOWS_ANSWERS = True
PRACTICE_MODE_ALLOWS_HINTS = True
PRACTICE_MODE_COUNTS_TOWARD_MASTERY = False

# Starting point choices
ALLOW_PREVIEW_SKIP = True  # Let learners skip directly to diagnostic
ALLOW_DIAGNOSTIC_RETRY = True  # Let learners restart diagnostic if unsure

# ============================================================================
# Encouragement & Motivation
# ============================================================================

# Struggle detection thresholds
STRUGGLE_THRESHOLD_MILD = 0.60      # 40-60% performance
STRUGGLE_THRESHOLD_MODERATE = 0.40  # Below 40% performance

# Recent questions to analyze for struggle detection
STRUGGLE_DETECTION_WINDOW = 5

# Encouragement message frequency
ENCOURAGEMENT_AFTER_N_INCORRECT = 2  # Show encouragement after 2+ wrong in a row

# ============================================================================
# Spaced Repetition with Forgiveness
# ============================================================================

# Learning phase settings (early attempts weighted less)
LEARNING_PHASE_QUESTIONS = 3  # First 3 questions are "learning phase"
LEARNING_PHASE_WEIGHT = 0.5   # Early questions weighted at 50%
MASTERY_PHASE_WEIGHT = 1.0    # Later questions weighted at 100%

# ============================================================================
# Celebration Milestones
# ============================================================================

# Streak detection
CELEBRATION_STREAK_SHORT = 3   # "3 in a row!"
CELEBRATION_STREAK_MEDIUM = 5  # "5 in a row - you're on fire!"
CELEBRATION_STREAK_LONG = 10   # "10 in a row - unstoppable!"

# Milestone events
CELEBRATE_FIRST_CONCEPT = True
CELEBRATE_HALFWAY_POINT = True  # 50% of concepts completed
CELEBRATE_FINAL_CONCEPT = True

# Performance milestones
CELEBRATION_MASTERY_ACHIEVED = True
CELEBRATION_COMEBACK = True  # Recovered from struggle (< 40% → > 70%)

# ============================================================================
# Hint System (Practice Mode)
# ============================================================================

# Hint availability
HINTS_ENABLED_IN_PRACTICE = True
HINTS_ENABLED_IN_GRADED = False  # Only in practice mode
MAX_HINTS_PER_QUESTION = 2      # Two-level hints (gentle → direct)

# Hint types
HINT_LEVEL_GENTLE = "gentle"      # Indirect hint (e.g., "Think about case endings...")
HINT_LEVEL_DIRECT = "direct"      # Direct hint (e.g., "The -ae ending indicates...")
HINT_LEVEL_ANSWER = "answer"      # Show answer with explanation
