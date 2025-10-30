-- Content Cache Database Schema
-- Stores dynamically generated and cached content for reuse

-- Main content cache table
CREATE TABLE IF NOT EXISTS content_cache (
    id TEXT PRIMARY KEY,  -- UUID

    -- Content identification
    course_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    content_type TEXT NOT NULL,  -- 'explanation', 'question', 'feedback', 'example'

    -- Tagging for intelligent retrieval
    tags TEXT NOT NULL,  -- JSON: {"stage": "start", "learning_style": "visual", "correctness": true}

    -- The actual content
    content_data TEXT NOT NULL,  -- JSON: full content object

    -- Effectiveness tracking
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,  -- How many learners succeeded after viewing
    success_rate REAL GENERATED ALWAYS AS (
        CASE
            WHEN usage_count > 0 THEN CAST(success_count AS REAL) / usage_count
            ELSE 0.0
        END
    ) VIRTUAL,

    avg_time_to_mastery REAL,  -- Average hours to mastery after viewing this content

    -- Metadata
    generated_by TEXT NOT NULL,  -- 'pre-gen', 'ai-cache', 'on-demand'
    created_at TEXT NOT NULL,  -- ISO timestamp
    last_used_at TEXT,  -- ISO timestamp

    -- Performance optimization
    effectiveness_score REAL DEFAULT 0.5,  -- 0.0-1.0, updated based on outcomes

    UNIQUE(course_id, concept_id, content_type, tags)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_content_lookup
ON content_cache(course_id, concept_id, content_type, effectiveness_score DESC);

CREATE INDEX IF NOT EXISTS idx_tags
ON content_cache(tags);

-- Content usage tracking table
CREATE TABLE IF NOT EXISTS content_usage (
    id TEXT PRIMARY KEY,  -- UUID
    content_id TEXT NOT NULL,
    learner_id TEXT NOT NULL,

    -- Outcome tracking
    was_effective INTEGER,  -- Boolean: 0=no, 1=yes, NULL=unknown yet
    learner_score REAL,  -- Score on next assessment
    time_to_mastery REAL,  -- Hours from viewing to mastery

    -- Context
    learner_context TEXT,  -- JSON: learner state when content was shown

    -- Metadata
    viewed_at TEXT NOT NULL,  -- ISO timestamp
    outcome_determined_at TEXT,  -- ISO timestamp when effectiveness was determined

    FOREIGN KEY (content_id) REFERENCES content_cache(id)
);

CREATE INDEX IF NOT EXISTS idx_usage_lookup
ON content_usage(content_id, was_effective);

CREATE INDEX IF NOT EXISTS idx_learner_usage
ON content_usage(learner_id, viewed_at);

-- Statistics view for easy querying
CREATE VIEW IF NOT EXISTS content_effectiveness_stats AS
SELECT
    c.id,
    c.course_id,
    c.concept_id,
    c.content_type,
    c.tags,
    c.usage_count,
    c.success_rate,
    c.effectiveness_score,
    COUNT(u.id) as total_views,
    AVG(CASE WHEN u.was_effective = 1 THEN 1.0 ELSE 0.0 END) as measured_effectiveness,
    AVG(u.time_to_mastery) as avg_mastery_time
FROM content_cache c
LEFT JOIN content_usage u ON c.id = u.content_id
GROUP BY c.id;
