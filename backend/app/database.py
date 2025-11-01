"""
Database management for the Latin Learning app.
"""

import sqlite3
import logging
from .config import config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create the necessary database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Learners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learners (
        id TEXT PRIMARY KEY,
        name TEXT,
        profile TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        learner_id TEXT,
        concept_id TEXT,
        messages TEXT,
        FOREIGN KEY (learner_id) REFERENCES learners (id)
    )
    """)

    conn.commit()
    conn.close()
    logger.info("Database tables created or already exist.")

def init_db():
    """Initialize the database."""
    create_tables()
