"""
Pydantic schemas for the Latin Learning app.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

class StartRequest(BaseModel):
    """Request to start a new learner session."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    learner_name: Optional[str] = Field(None, description="Learner's name")
    profile: Optional[Dict[str, Any]] = Field(None, description="Learner profile from onboarding")
    course_id: Optional[str] = Field(None, description="Course ID to enroll in")

class ChatRequest(BaseModel):
    """Request to send a chat message."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    message: str = Field(..., description="User's message to the tutor")
    conversation_history: Optional[List[dict]] = Field(None, description="Previous conversation messages")

class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    success: bool
    message: str
    conversation_history: List[dict]
    error: Optional[str] = None

class ProgressResponse(BaseModel):
    """Response with learner progress information."""
    learner_id: str
    current_concept: str
    concepts_completed: int
    concepts_in_progress: int
    total_assessments: int
    average_calibration_accuracy: float
    concept_details: dict
    overall_calibration: Optional[dict] = None

class ConceptResponse(BaseModel):
    """Response with concept information."""
    concept_id: str
    title: str
    difficulty: str  # Can be string like "medium" or "easy"
    prerequisites: List[str]
    learning_objectives: List[str]
    estimated_mastery_time: str
    vocabulary: List[dict]

class MasteryResponse(BaseModel):
    """Response with mastery information."""
    concept_id: str
    mastery_achieved: bool
    mastery_score: float
    assessments_completed: int
    recommendation: str
    reason: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str

class SubmitResponseRequest(BaseModel):
    """Request to submit and evaluate a learner response."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    question_type: str = Field(..., description="Type of question (multiple-choice, fill-blank, dialogue)")
    user_answer: Any = Field(..., description="Learner's answer (index for MC, string for others)")
    correct_answer: Any = Field(..., description="Correct answer")
    confidence: Optional[int] = Field(None, ge=1, le=4, description="Confidence level (1-4 stars), optional for adaptive frequency")
    current_concept: str = Field(..., description="Concept being tested")
    question_text: Optional[str] = Field(None, description="The question text")
    scenario_text: Optional[str] = Field(None, description="The scenario text (if any)")
    options: Optional[List[str]] = Field(None, description="List of answer options for multiple-choice questions")

class EvaluationResponse(BaseModel):
    """Response after evaluating a learner's answer."""
    is_correct: bool
    confidence: Optional[int] = None  # Optional when confidence slider is disabled
    calibration_type: Optional[str] = None  # Optional when no confidence rating
    feedback_message: str
    mastery_score: float  # Add mastery tracking
    mastery_threshold: float
    assessments_count: int
    concept_completed: bool
    next_content: dict  # The next piece of content to show
    debug_context: Optional[dict] = None  # Debug info showing what was sent to AI

class TutorConversationRequest(BaseModel):
    """Request to start or continue a tutor conversation."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")

class TutorConversationResponse(BaseModel):
    """Response from tutor conversation endpoint."""
    success: bool
    conversation_id: str
    message: str  # The tutor's response
    conversation_history: List[dict]
    error: Optional[str] = None

class ConversationHistoryRequest(BaseModel):
    """Request to get conversation history."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: Optional[str] = Field(None, description="Filter by concept (optional)")
    conversation_type: Optional[str] = Field(None, description="Filter by type: 'tutor' or 'roman' (optional)")
    hours: int = Field(24, description="Get conversations from last N hours")
    limit: int = Field(10, description="Maximum number of conversations to return")

class StruggleDetectionResponse(BaseModel):
    """Response from struggle detection endpoint."""
    is_struggling: bool
    topics: List[str] = []
    recommendation: Optional[str] = None
    intervention: Optional[str] = None

class RomanConversationRequest(BaseModel):
    """Request to start or continue a Roman character conversation."""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")
    scenario_id: Optional[str] = Field(None, description="Specific scenario to use (optional)")

class RomanConversationResponse(BaseModel):
    """Response from Roman conversation endpoint."""
    success: bool
    conversation_id: str
    message: str  # The Roman character's response
    conversation_history: List[dict]
    scenario: dict  # Scenario information (character name, setting, etc.)
    error: Optional[str] = None

class ScenariosListResponse(BaseModel):
    """List of available scenarios for a concept."""
    concept_id: str
    scenarios: List[dict]

class CourseMetadata(BaseModel):
    """Course metadata structure."""
    model_config = {"extra": "allow", "validate_default": False}

    course_id: str
    title: str
    domain: str
    taxonomy: Optional[str] = "blooms"
    course_learning_outcomes: List[str] = Field(default_factory=list)
    onboarding_questions: Optional[List[dict]] = Field(default_factory=list)
    # Keep these for backward compatibility with old courses
    description: Optional[str] = None
    target_audience: Optional[str] = None
    created_at: str
    updated_at: str
    concepts: List[dict] = Field(default_factory=list)

class CreateCourseRequest(BaseModel):
    """Request to create a new course."""
    course_id: str = Field(..., description="Unique course identifier (e.g., 'spanish-101')")
    title: str = Field(..., description="Course title")
    domain: str = Field(..., description="Subject area")
    taxonomy: str = Field(default="blooms", description="Learning outcome framework (blooms, finks, or both)")
    course_learning_outcomes: List[str] = Field(default=[], description="Course-level learning outcomes (CLOs)")
    # Keep these for backward compatibility with old courses
    description: Optional[str] = Field(default=None, description="Course description (deprecated)")
    target_audience: Optional[str] = Field(default=None, description="Target audience (deprecated)")
    # Support both flat concepts (old) and module-based structure (new)
    concepts: List[dict] = Field(default=[], description="Flat list of course concepts (deprecated - use modules)")
    modules: List[dict] = Field(default=[], description="Module-based course structure (each module contains concepts)")

class ImportCourseRequest(BaseModel):
    """Request to import a course from exported JSON."""
    export_data: dict = Field(..., description="Exported course JSON data")
    new_course_id: Optional[str] = Field(default=None, description="Optional new course ID (overrides exported ID)")
    overwrite: bool = Field(default=False, description="Overwrite existing course if it exists")

class CoursesListResponse(BaseModel):
    """Response with list of available courses."""
    courses: List[dict]
    total: int

class AddSourceRequest(BaseModel):
    """Request to add an external source to a course or concept."""
    url: str = Field(..., description="Source URL")
    source_type: Optional[str] = Field(None, description="Source type (auto-detected if not provided)")
    title: Optional[str] = Field(None, description="Optional custom title")
    description: Optional[str] = Field(None, description="Optional custom description")
    requirement_level: Optional[str] = Field(default="optional", description="Requirement level: optional, recommended, or required")
    verification_method: Optional[str] = Field(default="none", description="Verification method: none, self-attestation, comprehension-quiz, or discussion-prompt")
    verification_data: Optional[dict] = Field(default=None, description="Verification data (quiz questions, discussion prompts, etc.)")

class SourceResponse(BaseModel):
    """Response with source metadata."""
    source_id: str
    type: str
    url: str
    title: str
    description: str
    metadata: dict
    added_at: str
    status: str
    error_message: Optional[str] = None

class SourceContentResponse(BaseModel):
    """Response with full source content."""
    success: bool
    content: Optional[str] = None
    content_type: str
    length: Optional[int] = None
    error: Optional[str] = None
