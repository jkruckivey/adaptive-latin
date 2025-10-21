# Adaptive AI-Driven Self-Paced Learning System
## Project Architecture

**Version**: 0.1.0 (Planning Phase)
**Target**: Proof of Concept
**Scope**: Domain-agnostic framework
**Created**: 2025-10-21

---

## Executive Summary

A truly adaptive learning system where an AI agent continuously assesses learners and dynamically sequences content from a pre-built resource bank. The entire learning experience IS the assessment - progression and regression are determined in real-time based on demonstrated understanding.

### Core Principles
- **Continuous Assessment**: No separation between learning and testing
- **Mastery-Based Progression**: Advance only when ready, review when needed
- **Adaptive Sequencing**: Same resources, personalized order and pacing
- **Multi-Modal Assessment**: Conversation, writing, applied tasks, self-reflection

---

## System Architecture

### 1. Resource Bank (Content Library)

**Purpose**: Pre-authored learning resources organized by concepts/competencies

**Structure**:
```
resource-bank/
├── concepts/
│   ├── concept-001/
│   │   ├── metadata.json          # Prerequisites, difficulty, learning objectives
│   │   ├── resources/
│   │   │   ├── text-explainer.md  # Written explanation
│   │   │   ├── video-lecture.mp4  # Video content
│   │   │   ├── principle.md       # Core principle/framework
│   │   │   └── examples.json      # Worked examples
│   │   └── assessments/
│   │       ├── dialogue-prompts.json     # Socratic questions
│   │       ├── written-prompts.json      # Essay/reflection prompts
│   │       ├── applied-tasks.json        # Case studies, problems
│   │       └── self-check-criteria.json  # Self-assessment rubrics
│   └── concept-002/
│       └── ...
├── learning-paths/
│   ├── default-sequence.json      # Standard concept ordering
│   └── prerequisite-graph.json    # Concept dependencies
└── global-resources/
    ├── study-strategies.md
    └── meta-learning-guidance.md
```

**Metadata Schema** (concept-XXX/metadata.json):
```json
{
  "id": "concept-001",
  "title": "Supply and Demand Equilibrium",
  "domain": "economics",
  "difficulty": 2,
  "prerequisites": ["concept-000"],
  "learning_objectives": [
    "Explain how supply and demand determine market equilibrium",
    "Calculate equilibrium price and quantity given supply/demand curves"
  ],
  "estimated_mastery_time": "45-90 minutes",
  "available_resource_types": ["text", "video", "examples"],
  "assessment_types": ["dialogue", "written", "applied"]
}
```

---

### 2. AI Agent (Orchestration Engine)

**Purpose**: Intelligent tutor that assesses understanding and sequences learning

**Core Responsibilities**:
1. **Assessment**: Evaluate learner responses across all modalities
2. **Diagnosis**: Identify knowledge gaps, misconceptions, readiness
3. **Sequencing**: Select next concept or decide to review/regress
4. **Resource Selection**: Choose appropriate materials from resource bank
5. **Interaction**: Engage learner through dialogue, prompts, tasks

**Agent Prompting Architecture**:
```
System Prompt:
- Role: Adaptive learning tutor
- Goal: Guide learner to mastery through continuous assessment
- Capabilities: Access to resource bank, learner model, assessment rubrics
- Constraints: Only progress when mastery demonstrated

Context (Updated Each Interaction):
- Current learner model (progress, understanding levels, history)
- Current concept metadata
- Available resources and assessment options
- Conversation history

Decision Loop:
1. Assess latest learner response
2. Update learner model
3. Determine action:
   a. Continue current concept (more assessment needed)
   b. Progress to next concept (mastery achieved)
   c. Regress to prerequisite (gap identified)
   d. Provide targeted support/resources
4. Execute action
5. Log decision rationale
```

---

### 3. Learner Model (Progress Tracker)

**Purpose**: Persistent state tracking learner's knowledge and progress

**Schema** (learner-model.json):
```json
{
  "learner_id": "learner-001",
  "current_concept": "concept-003",
  "learning_path": ["concept-000", "concept-001", "concept-002", "concept-003"],
  "concept_mastery": {
    "concept-000": {
      "status": "mastered",
      "confidence": 0.95,
      "attempts": 2,
      "time_spent_minutes": 60,
      "assessment_scores": {
        "dialogue": 0.9,
        "written": 1.0,
        "applied": 0.95
      },
      "last_assessed": "2025-10-15T14:30:00Z"
    },
    "concept-001": {
      "status": "mastered",
      "confidence": 0.85,
      "attempts": 3,
      "time_spent_minutes": 90,
      "assessment_scores": {
        "dialogue": 0.8,
        "written": 0.85,
        "applied": 0.9
      },
      "last_assessed": "2025-10-16T10:15:00Z"
    },
    "concept-002": {
      "status": "reviewing",
      "confidence": 0.65,
      "attempts": 1,
      "time_spent_minutes": 45,
      "assessment_scores": {
        "dialogue": 0.6,
        "written": 0.7
      },
      "identified_gaps": ["Misunderstanding of edge cases"],
      "last_assessed": "2025-10-17T09:00:00Z"
    }
  },
  "overall_progress": 0.60,
  "learning_preferences": {
    "response_style": "conversational",
    "self_assessment_accuracy": 0.75
  },
  "session_history": [
    {
      "session_id": "session-001",
      "date": "2025-10-15",
      "concepts_covered": ["concept-000"],
      "duration_minutes": 60,
      "interactions": 12
    }
  ]
}
```

**Mastery Criteria**:
- **Dialogue Assessment**: ≥ 0.80 (demonstrates clear explanation, handles edge cases)
- **Written Assessment**: ≥ 0.80 (depth of understanding, correct application)
- **Applied Assessment**: ≥ 0.80 (correct solutions, sound reasoning)
- **Overall Confidence**: ≥ 0.85 (composite score across all assessments)
- **Consistency**: No major contradictions across assessment types

**Regression Triggers**:
- Current concept confidence < 0.70 after 2+ attempts
- Identified gaps in prerequisite concepts
- Persistent misconceptions despite targeted support

---

### 4. Assessment Engine

**Purpose**: Evaluate learner responses across multiple modalities

**Assessment Types**:

**A. Conversational Dialogue**
- AI asks Socratic questions from dialogue-prompts.json
- Evaluates: clarity, accuracy, handling of edge cases, depth
- Scoring rubric embedded in AI prompt
- Example:
  ```
  AI: "Can you explain why the demand curve slopes downward?"
  Learner: [responds]
  AI Evaluation:
  - Correct explanation? (0.5 points)
  - Mentioned substitution effect? (0.25 points)
  - Mentioned income effect? (0.25 points)
  - Score: 0.85 (if 3.4/4 points)
  ```

**B. Written Responses**
- AI provides prompt from written-prompts.json
- Learner writes short answer/essay/reflection
- AI evaluates using rubric: thesis, evidence, reasoning, depth
- Score: 0-1.0

**C. Applied Tasks**
- AI presents case study/problem from applied-tasks.json
- Learner submits solution/analysis
- AI evaluates: correctness, process, reasoning
- Score: 0-1.0

**D. Self-Assessment + Validation**
- Learner rates own understanding using self-check-criteria.json
- AI validates with targeted follow-up questions
- Tracks self-assessment accuracy over time
- Adjusts trust in self-reports based on historical accuracy

**Assessment Logging**:
```json
{
  "assessment_id": "assess-123",
  "timestamp": "2025-10-17T10:30:00Z",
  "concept_id": "concept-002",
  "assessment_type": "dialogue",
  "prompt": "Explain how a price ceiling affects market equilibrium",
  "learner_response": "...",
  "ai_evaluation": {
    "score": 0.75,
    "rubric_breakdown": {
      "accuracy": 0.8,
      "completeness": 0.7,
      "edge_cases": 0.75
    },
    "identified_gaps": ["Didn't mention deadweight loss"],
    "feedback": "Good explanation of shortage, but consider welfare effects..."
  },
  "updated_confidence": 0.72
}
```

---

### 5. Interaction Interface (Learner Experience)

**Purpose**: How learners engage with the AI agent

**Modes**:

**A. Guided Dialogue Mode** (Primary)
- Chat-based interface
- AI introduces concept, provides resources
- Learner reads/watches, asks questions
- AI assesses through conversation
- AI determines when to progress

**B. Task Submission Mode**
- AI assigns written response or applied task
- Learner submits work
- AI evaluates and provides feedback
- May trigger follow-up dialogue if gaps detected

**C. Self-Assessment Mode**
- AI provides self-check criteria
- Learner reflects and rates understanding
- AI validates with targeted questions
- Builds metacognitive skills

**Example Session Flow**:
```
[Session Start - Concept 003: Price Elasticity]

AI: "You've mastered supply and demand equilibrium. Let's explore price
     elasticity of demand. First, watch this 8-minute video: [link]"

[Learner watches video]

AI: "In your own words, what does it mean for demand to be elastic?"

Learner: [responds]

AI: [Evaluates response, asks follow-up based on quality]
    "Good start. Can you give me an example of a product with elastic demand?"

Learner: [provides example]

AI: [If response shows understanding]
    "Excellent. Now let's apply this. Here's a case study: [presents scenario]"

Learner: [works through case]

AI: [Evaluates applied task]
    [If mastery demonstrated] "You've shown strong understanding. Ready for
                              the next concept: cross-price elasticity?"
    [If gaps identified] "I noticed some confusion about the midpoint formula.
                          Let's review that before moving forward..."
```

---

### 6. Progression Logic

**Purpose**: Decision-making rules for moving forward/backward

**Decision Tree**:

```
After Each Assessment:

1. Calculate current concept confidence
   └─ If confidence ≥ 0.85 AND all assessment types attempted
      └─ PROGRESS to next concept
      └─ Log mastery achievement
      └─ Update learner model

   └─ If confidence 0.70-0.84
      └─ CONTINUE current concept
      └─ Provide targeted support for identified gaps
      └─ Attempt additional assessment in weak area

   └─ If confidence < 0.70 after 2+ attempts
      └─ DIAGNOSE root cause
      └─ If prerequisite gap identified:
         └─ REGRESS to prerequisite concept
         └─ Explain rationale to learner
         └─ Mark current concept as "deferred"
      └─ If misconception identified:
         └─ PROVIDE targeted explanation
         └─ REASSESS with different prompt
      └─ If struggling with assessment type:
         └─ SWITCH to different assessment modality
         └─ Example: If written weak, try dialogue

2. Check for overall course completion
   └─ If all concepts mastered:
      └─ COMPLETE course
      └─ Provide summary and next steps
```

**Transparency**:
- AI always explains progression decisions to learner
- Example: "You've demonstrated mastery of price elasticity (confidence: 0.88).
           Ready to move on to cross-price elasticity, which builds on this concept."
- Example: "I noticed some confusion about calculating elasticity coefficients.
           Let's spend more time on this before moving forward. Here's another
           way to think about it..."

---

## Technical Implementation Stack (Proof of Concept)

### Backend
- **AI Model**: Claude 3.5 Sonnet (via Anthropic API)
- **Resource Storage**: File system (JSON/Markdown)
- **Learner Model Storage**: JSON files (upgrade to database later)
- **Orchestration**: Python backend with FastAPI

### Frontend
- **Interface**: Simple web chat UI (React or vanilla JS)
- **Features**:
  - Chat messages
  - Resource display (text, embedded video)
  - Task submission forms
  - Progress dashboard (concept map with current position)

### AI Agent Implementation
- **Prompt Templates**: Stored in `prompts/` directory
- **Tool Use**: Claude API with tool calling for:
  - `load_resource(concept_id, resource_type)` - Fetch from resource bank
  - `update_learner_model(concept_id, assessment_data)` - Update progress
  - `calculate_mastery(concept_id)` - Check if ready to progress
  - `get_next_concept(current_id, learner_model)` - Determine sequencing

### Data Flow
```
Learner Input
  → FastAPI Backend
  → Claude API (with context: learner model + resource bank + prompts)
  → AI Decision (assess, sequence, respond)
  → Update Learner Model
  → Return Response to Frontend
  → Display to Learner
```

---

## Proof of Concept Scope

### Phase 1: Minimal Viable System (6-8 weeks)

**What to Build**:
1. **Resource Bank**: 5-7 concepts in a single domain (e.g., microeconomics)
   - Each concept: 1 text resource, 1 video, 3 assessment prompts (dialogue, written, applied)
   - Total: ~35-50 resources

2. **AI Agent**: Single-prompt orchestrator
   - Context: Current concept, learner history, assessment rubrics
   - Actions: Assess, provide feedback, sequence next step
   - Tool use: Load resources, update model, check mastery

3. **Learner Model**: JSON file per learner
   - Track concept progress, confidence scores, assessment history

4. **Interface**: Basic web chat
   - Chat window for dialogue
   - Text area for written responses
   - Simple progress indicator (5/7 concepts mastered)

5. **Testing**: 1-2 learners (pilot users)
   - Manual observation of agent decisions
   - Log all interactions for analysis
   - Collect feedback on experience

**Success Criteria**:
- Agent successfully assesses understanding across 3 modalities
- Agent correctly identifies when to progress/regress
- Agent provides helpful feedback that improves learner understanding
- Learners report feeling "tutored" rather than "tested"
- System completes full learning path (all 5-7 concepts) with at least 1 learner

**What NOT to Build**:
- User authentication
- Multiple simultaneous learners
- Advanced analytics/reporting
- Resource creation tools
- Mobile interface
- Instructor dashboard

---

## Key Design Decisions

### 1. Why Adaptive Sequencing Only (not resource variation)?
- Simplifies PoC - one resource set per concept
- Focuses validation on core innovation: continuous assessment + dynamic sequencing
- Can add resource variation in future if sequencing works well

### 2. Why Multiple Assessment Modalities?
- Richer picture of understanding than single test type
- Validates mastery from different angles
- Reduces false positives (learner might memorize answer to one prompt type)

### 3. Why File-Based Storage for PoC?
- Faster to implement than database
- Easy to inspect/debug learner models
- Version control friendly
- Sufficient for 1-2 pilot learners

### 4. Why Claude 3.5 Sonnet?
- Strong reasoning for assessment evaluation
- Nuanced feedback generation
- Tool use for resource orchestration
- Extended context window for learner history

---

## Open Questions / Future Considerations

1. **Mastery Thresholds**: Are 0.85 confidence scores the right bar? May need tuning based on PoC data.

2. **Assessment Fatigue**: How many assessments before learner frustration? May need "help" mechanisms.

3. **Remediation Strategies**: When regression happens, what's the optimal re-teaching approach?

4. **Domain Differences**: Will economics concepts work the same as programming concepts? Framework should be domain-agnostic, but may need domain-specific assessment rubrics.

5. **Scalability**: If successful, how to author resources at scale? May need LLM-assisted resource generation.

6. **Instructor Role**: In production system, how do human instructors fit? Monitor? Intervene? Author resources?

7. **Learning Analytics**: What data should we track to improve the system over time?

---

## Next Steps (Immediate)

1. **Choose pilot domain** for 5-7 concepts (e.g., microeconomics fundamentals)
2. **Author resource bank** for those concepts
3. **Write AI agent prompt** with assessment rubrics and sequencing logic
4. **Build minimal backend** (FastAPI + Claude API integration)
5. **Build minimal frontend** (chat UI + progress display)
6. **Test with 1 learner** (could be yourself initially)
7. **Iterate based on observed agent behavior**

---

## Success Metrics (PoC Evaluation)

**Agent Performance**:
- Accuracy of mastery assessments (manual review of agent decisions)
- Appropriateness of progression/regression decisions
- Quality of feedback provided to learners

**Learner Experience**:
- Time to complete learning path
- Number of regressions needed
- Subjective satisfaction ratings
- Comparison to traditional linear course on same content

**System Viability**:
- Can this scale beyond 1-2 learners?
- Is resource bank authoring sustainable?
- Are assessment rubrics generalizable across domains?

---

## Related Work / Inspiration

- **Intelligent Tutoring Systems (ITS)**: ALEKS, Carnegie Learning
- **Adaptive Learning Platforms**: Khan Academy, Duolingo
- **Mastery-Based Learning**: Bloom's Learning for Mastery (1968)
- **AI Tutoring**: GPT-based tutors, but most lack persistent learner models + true sequencing

**Differentiation**: This system integrates continuous multi-modal assessment with dynamic sequencing in a domain-agnostic framework, powered by modern LLMs.
