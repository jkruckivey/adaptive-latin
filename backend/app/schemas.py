"""
Pydantic schemas for the Latin Learning app.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

class StartRequest(BaseModel):
    learner_id: str = Field(..., description="Unique identifier for the learner")
    learner_name: Optional[str] = Field(None, description="Learner's name")
    profile: Optional[Dict[str, Any]] = Field(None, description="Learner profile from onboarding")

class ChatRequest(BaseModel):
    learner_id: str = Field(..., description="Unique identifier for the learner")
    message: str = Field(..., description="User's message to the tutor")
    conversation_history: Optional[List[dict]] = Field(None, description="Previous conversation messages")

class ChatResponse(BaseModel):
    success: bool
    message: str
    conversation_history: List[dict]
    error: Optional[str] = None

class ProgressResponse(BaseModel):
    learner_id: str
    current_concept: str
    concepts_completed: int
    concepts_in_progress: int
    total_assessments: int
    average_calibration_accuracy: float
    concept_details: dict
    overall_calibration: Optional[dict] = None

class ConceptResponse(BaseModel):
    concept_id: str
    title: str
    difficulty: int
    prerequisites: List[str]
    learning_objectives: List[str]
    estimated_mastery_time: str
    vocabulary: List[dict]

class MasteryResponse(BaseModel):
    concept_id: str
    mastery_achieved: bool
    mastery_score: float
    assessments_completed: int
    recommendation: str
    reason: str

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

class SubmitResponseRequest(BaseModel):
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
    is_correct: bool
    confidence: Optional[int] = None
    calibration_type: Optional[str] = None
    feedback_message: str
    mastery_score: float
    mastery_threshold: float
    assessments_count: int
    concept_completed: bool
    next_content: dict
    debug_context: Optional[dict] = None

class TutorConversationRequest(BaseModel):
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")

class TutorConversationResponse(BaseModel):
    success: bool
    conversation_id: str
    message: str
    conversation_history: List[dict]
    error: Optional[str] = None

class RomanConversationRequest(BaseModel):
    learner_id: str = Field(..., description="Unique identifier for the learner")
    concept_id: str = Field(..., description="Current concept being studied")
    message: Optional[str] = Field(None, description="User message (None to start new conversation)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None to start new)")
    scenario_id: Optional[str] = Field(None, description="Specific scenario to use (optional)")

class RomanConversationResponse(BaseModel):
    success: bool
    conversation_id: str
    message: str
    conversation_history: List[dict]
    scenario: dict
    error: Optional[str] = None

class ScenariosListResponse(BaseModel):
    concept_id: str
    scenarios: List[dict]

class StruggleDetectionResponse(BaseModel):
    is_struggling: bool
    topics: List[str] = []
    recommendation: Optional[str] = None
    intervention: Optional[str] = None
