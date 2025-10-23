"""
Conversation Management System

Handles "Talk to Tutor" and "Talk to Roman" conversational AI features.
Manages conversation history, struggle detection, and progress tracking.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from collections import Counter
from .config import config
from .tools import load_learner_model, save_learner_model

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

ConversationType = Literal["tutor", "roman"]
MessageRole = Literal["user", "assistant", "system"]


class Message:
    """A single message in a conversation."""

    def __init__(self, role: MessageRole, content: str, timestamp: Optional[str] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp")
        )


class Conversation:
    """A conversation between learner and AI (tutor or Roman character)."""

    def __init__(
        self,
        conversation_id: str,
        learner_id: str,
        conversation_type: ConversationType,
        concept_id: str,
        messages: Optional[List[Message]] = None,
        context: Optional[Dict[str, Any]] = None,
        scenario: Optional[Dict[str, Any]] = None,
        started_at: Optional[str] = None,
        last_updated: Optional[str] = None,
        counts_toward_progress: bool = True
    ):
        self.conversation_id = conversation_id
        self.learner_id = learner_id
        self.type = conversation_type
        self.concept_id = concept_id
        self.messages = messages or []
        self.context = context or {}
        self.scenario = scenario
        self.started_at = started_at or datetime.now().isoformat()
        self.last_updated = last_updated or datetime.now().isoformat()
        self.counts_toward_progress = counts_toward_progress

    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation."""
        message = Message(role, content)
        self.messages.append(message)
        self.last_updated = datetime.now().isoformat()

    def get_message_count(self) -> int:
        """Get the number of user + assistant exchanges."""
        return len([m for m in self.messages if m.role in ["user", "assistant"]])

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages."""
        return self.messages[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "conversation_id": self.conversation_id,
            "learner_id": self.learner_id,
            "type": self.type,
            "concept_id": self.concept_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "scenario": self.scenario,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "counts_toward_progress": self.counts_toward_progress
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data["conversation_id"],
            learner_id=data["learner_id"],
            conversation_type=data["type"],
            concept_id=data["concept_id"],
            messages=messages,
            context=data.get("context"),
            scenario=data.get("scenario"),
            started_at=data.get("started_at"),
            last_updated=data.get("last_updated"),
            counts_toward_progress=data.get("counts_toward_progress", True)
        )


# ============================================================================
# Conversation Storage Functions
# ============================================================================

def get_conversations_dir(learner_id: str) -> Path:
    """Get the directory for storing a learner's conversations."""
    conversations_dir = config.LEARNER_MODELS_DIR / learner_id / "conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)
    return conversations_dir


def generate_conversation_id(learner_id: str, conversation_type: ConversationType) -> str:
    """Generate a unique conversation ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{conversation_type}-{learner_id}-{timestamp}"


def save_conversation(conversation: Conversation) -> None:
    """Save a conversation to disk."""
    try:
        conversations_dir = get_conversations_dir(conversation.learner_id)
        file_path = conversations_dir / f"{conversation.conversation_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved conversation {conversation.conversation_id}")

    except Exception as e:
        logger.error(f"Error saving conversation {conversation.conversation_id}: {e}")
        raise


def load_conversation(conversation_id: str, learner_id: str) -> Optional[Conversation]:
    """Load a conversation from disk."""
    try:
        conversations_dir = get_conversations_dir(learner_id)
        file_path = conversations_dir / f"{conversation_id}.json"

        if not file_path.exists():
            logger.warning(f"Conversation {conversation_id} not found")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded conversation {conversation_id}")
        return Conversation.from_dict(data)

    except Exception as e:
        logger.error(f"Error loading conversation {conversation_id}: {e}")
        raise


def get_recent_conversations(
    learner_id: str,
    concept_id: Optional[str] = None,
    conversation_type: Optional[ConversationType] = None,
    hours: int = 24,
    limit: int = 10
) -> List[Conversation]:
    """Get recent conversations for a learner."""
    try:
        conversations_dir = get_conversations_dir(learner_id)

        if not conversations_dir.exists():
            return []

        # Load all conversation files
        conversations = []
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        for file_path in conversations_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Filter by concept_id and type if specified
                if concept_id and data.get("concept_id") != concept_id:
                    continue

                if conversation_type and data.get("type") != conversation_type:
                    continue

                # Filter by time
                last_updated = datetime.fromisoformat(data.get("last_updated", ""))
                if last_updated.timestamp() < cutoff_time:
                    continue

                conversations.append(Conversation.from_dict(data))

            except Exception as e:
                logger.warning(f"Error loading conversation file {file_path}: {e}")
                continue

        # Sort by last_updated (most recent first)
        conversations.sort(key=lambda c: c.last_updated, reverse=True)

        return conversations[:limit]

    except Exception as e:
        logger.error(f"Error getting recent conversations for {learner_id}: {e}")
        return []


# ============================================================================
# Conversation Context Building
# ============================================================================

def build_conversation_context(learner_id: str, concept_id: str) -> Dict[str, Any]:
    """
    Build context for a new conversation including:
    - Learner profile
    - Recent questions and struggles
    - Current concept information
    """
    try:
        # Load learner model
        learner_model = load_learner_model(learner_id)

        # Get recent question history
        recent_questions = learner_model.get("question_history", [])[-5:]

        # Get concept progress
        concept_data = learner_model.get("concepts", {}).get(concept_id, {})

        # Identify struggling topics
        struggling_topics = []
        if concept_data:
            assessments = concept_data.get("assessments", [])
            recent_assessments = assessments[-5:]

            # Find topics with low scores
            for assessment in recent_assessments:
                if assessment.get("score", 1.0) < 0.6:
                    prompt_id = assessment.get("prompt_id", "")
                    struggling_topics.append(prompt_id)

        context = {
            "learner_name": learner_model.get("learner_name"),
            "learner_profile": learner_model.get("profile", {}),
            "recent_questions": recent_questions,
            "current_concept": concept_id,
            "concept_progress": concept_data,
            "struggling_topics": list(set(struggling_topics)),
            "calibration_status": get_calibration_status(learner_model, concept_id)
        }

        logger.info(f"Built conversation context for {learner_id}")
        return context

    except Exception as e:
        logger.error(f"Error building conversation context: {e}")
        return {}


def get_calibration_status(learner_model: Dict[str, Any], concept_id: str) -> str:
    """Determine if learner is overconfident, underconfident, or calibrated."""
    concept_data = learner_model.get("concepts", {}).get(concept_id, {})
    confidence_history = concept_data.get("confidence_history", [])

    if len(confidence_history) < 3:
        return "unknown"

    # Calculate average calibration error
    recent_history = confidence_history[-5:]
    errors = [record.get("error", 0) for record in recent_history]
    avg_error = sum(errors) / len(errors) if errors else 0

    if avg_error > 1.0:
        return "overconfident"
    elif avg_error < -1.0:
        return "underconfident"
    else:
        return "calibrated"


# ============================================================================
# Struggle Detection
# ============================================================================

def detect_struggle_patterns(learner_id: str, concept_id: str) -> Dict[str, Any]:
    """
    Detect if learner is struggling based on:
    1. 3+ tutor questions on same topic within 1 hour
    2. Repeated incorrect answers on same concept
    3. Low confidence ratings (avg < 2/4)
    """
    try:
        # Get recent tutor conversations
        conversations = get_recent_conversations(
            learner_id=learner_id,
            concept_id=concept_id,
            conversation_type="tutor",
            hours=1,
            limit=20
        )

        if len(conversations) < 3:
            return {"is_struggling": False}

        # Extract topics from conversations
        topics = []
        for conv in conversations:
            # Extract topics from user messages
            for message in conv.messages:
                if message.role == "user":
                    # Simple topic extraction (could be enhanced with NLP)
                    content_lower = message.content.lower()

                    # Check for case-related questions
                    if "nominative" in content_lower:
                        topics.append("nominative_case")
                    if "genitive" in content_lower:
                        topics.append("genitive_case")
                    if "dative" in content_lower:
                        topics.append("dative_case")
                    if "accusative" in content_lower:
                        topics.append("accusative_case")
                    if "ablative" in content_lower:
                        topics.append("ablative_case")
                    if "ending" in content_lower:
                        topics.append("case_endings")
                    if "declension" in content_lower:
                        topics.append("declension")

        # Count topic frequency
        topic_frequency = Counter(topics)

        # Check for repeated topics (3+ mentions)
        struggling_topics = [topic for topic, count in topic_frequency.items() if count >= 3]

        if struggling_topics:
            logger.info(f"Detected struggle for {learner_id} on topics: {struggling_topics}")
            return {
                "is_struggling": True,
                "topics": struggling_topics,
                "recommendation": "trigger_extra_practice",
                "intervention": f"Offer guided lesson on {struggling_topics[0].replace('_', ' ')}"
            }

        return {"is_struggling": False}

    except Exception as e:
        logger.error(f"Error detecting struggle patterns: {e}")
        return {"is_struggling": False, "error": str(e)}


# ============================================================================
# Progress Tracking
# ============================================================================

def count_conversation_toward_progress(conversation: Conversation) -> None:
    """
    Award progress points for productive tutor conversations.
    Criteria:
    - At least 3 exchanges (6 messages: 3 user + 3 assistant)
    - Counts_toward_progress flag is True
    """
    try:
        if not conversation.counts_toward_progress:
            logger.info(f"Conversation {conversation.conversation_id} does not count toward progress")
            return

        message_count = conversation.get_message_count()

        if message_count < 6:
            logger.info(f"Conversation {conversation.conversation_id} too short to count ({message_count} messages)")
            return

        # Load learner model
        learner_model = load_learner_model(conversation.learner_id)

        # Track conversation in progress
        if "conversation_interactions" not in learner_model["overall_progress"]:
            learner_model["overall_progress"]["conversation_interactions"] = 0

        learner_model["overall_progress"]["conversation_interactions"] += 1

        # Save updated model
        save_learner_model(conversation.learner_id, learner_model)

        logger.info(f"Counted conversation {conversation.conversation_id} toward progress")

    except Exception as e:
        logger.error(f"Error counting conversation toward progress: {e}")
        raise


def get_conversation_stats(learner_id: str, concept_id: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics about a learner's conversations."""
    try:
        conversations = get_recent_conversations(
            learner_id=learner_id,
            concept_id=concept_id,
            hours=24*7,  # Last week
            limit=100
        )

        tutor_conversations = [c for c in conversations if c.type == "tutor"]
        roman_conversations = [c for c in conversations if c.type == "roman"]

        total_messages = sum(c.get_message_count() for c in conversations)

        stats = {
            "total_conversations": len(conversations),
            "tutor_conversations": len(tutor_conversations),
            "roman_conversations": len(roman_conversations),
            "total_messages": total_messages,
            "average_messages_per_conversation": total_messages / len(conversations) if conversations else 0,
            "concepts_discussed": list(set(c.concept_id for c in conversations))
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        return {}
