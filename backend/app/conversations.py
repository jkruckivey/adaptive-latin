"""
Conversation Management (with Database)
"""

import json
from typing import List, Optional
from .models import Conversation
from .database import get_db_connection
import logging

logger = logging.getLogger(__name__)


def save_conversation(conversation: Conversation):
    """Saves a conversation to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO conversations (id, learner_id, concept_id, messages)
        VALUES (?, ?, ?, ?)
        """,
        (
            conversation.conversation_id,
            conversation.learner_id,
            conversation.concept_id,
            json.dumps([m.to_dict() for m in conversation.messages])
        )
    )
    conn.commit()
    conn.close()
    logger.info(f"Saved conversation {conversation.conversation_id} to database")


def load_conversation(conversation_id: str, learner_id: str) -> Optional[Conversation]:
    """Loads a conversation from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM conversations WHERE id = ? AND learner_id = ?", (conversation_id, learner_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Recreate the Conversation object
    # This is a simplified example. You might need to deserialize messages into Message objects.
    conversation = Conversation(
        learner_id=row['learner_id'],
        concept_id=row['concept_id'],
        conversation_id=row['id']
    )
    conversation.messages = json.loads(row['messages'])

    logger.info(f"Loaded conversation {conversation_id} from database")
    return conversation

# ... (rest of the conversation logic)
