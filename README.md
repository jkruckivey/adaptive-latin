# Adaptive AI-Driven Self-Paced Learning System

An innovative learning platform where AI continuously assesses learners and dynamically sequences content for true mastery-based progression.

## Overview

This project implements a **domain-agnostic framework** for truly adaptive, self-paced learning where:

- The entire course IS an assessment - continuous evaluation, not periodic tests
- Learners progress when ready, regress when gaps are identified
- AI agent makes real-time decisions about sequencing based on demonstrated understanding
- Multi-modal assessment (dialogue, written, applied tasks) provides rich evidence of mastery

## Core Innovation

Traditional adaptive learning adjusts difficulty or provides hints. This system **adjusts the learning path itself** - deciding what concept comes next (or whether to review a previous one) based on continuous assessment of understanding.

## Project Status

**Phase**: Planning & Architecture
**Version**: 0.1.0
**Target**: Proof of Concept (6-8 weeks)
**Scope**: Single domain, 5-7 concepts, 1-2 pilot learners

## Documentation

### Start Here
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Comprehensive system design
   - Resource bank structure
   - AI agent orchestration
   - Learner model schema
   - Assessment engine
   - Progression logic
   - Technical stack

2. **[IMPLEMENTATION-ROADMAP.md](IMPLEMENTATION-ROADMAP.md)** - Step-by-step build guide
   - 4 phases over 6-8 weeks
   - Detailed tasks with time estimates
   - Code examples
   - Testing strategies
   - Success criteria

### Examples
- **[examples/resource-bank/concepts/concept-001/](examples/resource-bank/concepts/concept-001/)** - Complete example concept (Supply and Demand)
  - metadata.json - Learning objectives, difficulty, prerequisites
  - resources/text-explainer.md - Main teaching content
  - resources/examples.json - Worked examples
  - assessments/ - Dialogue, written, and applied assessment prompts with rubrics

- **[examples/prompts/tutor-agent-system-prompt.md](examples/prompts/tutor-agent-system-prompt.md)** - AI agent instructions
  - Assessment philosophy
  - Decision-making protocol
  - Conversation flow templates
  - Feedback principles

- **[examples/learner-models/learner-001-example.json](examples/learner-models/learner-001-example.json)** - Progress tracking
  - Concept mastery scores
  - Assessment history
  - Identified gaps
  - Session logs

## Key Concepts

### 1. Resource Bank
Pre-authored learning materials organized by concept:
- Text explanations
- Video content
- Worked examples
- Assessment prompts (dialogue, written, applied)
- Rubrics for evaluation

### 2. AI Agent (Tutor)
Intelligent orchestrator that:
- Introduces concepts and provides resources
- Assesses understanding through Socratic dialogue
- Evaluates written responses and applied tasks
- Calculates mastery confidence scores
- Decides when to progress, continue, or regress
- Provides personalized feedback

### 3. Learner Model
Persistent tracking of:
- Current concept and learning path
- Mastery confidence per concept (0.0-1.0)
- Assessment scores across modalities
- Identified knowledge gaps
- Session history

### 4. Assessment Engine
Multi-modal continuous assessment:
- **Dialogue**: Conversational questioning (Socratic method)
- **Written**: Short answer, essays, reflections
- **Applied**: Case studies, problem-solving, simulations
- **Self-Assessment**: Validated by AI follow-up

### 5. Progression Logic
Decision rules:
- **Progress** (confidence ≥ 0.85) → Next concept
- **Continue** (confidence 0.70-0.84) → More assessment, targeted support
- **Regress** (confidence < 0.70 after 2+ attempts) → Review prerequisites

## Quick Start (After Reading Docs)

### Prerequisites
- Python 3.10+
- Anthropic API key
- Text editor
- 65-85 hours over 6-8 weeks

### Setup
```bash
# Clone/create project directory
mkdir adaptive-learning-poc
cd adaptive-learning-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install anthropic fastapi uvicorn python-dotenv pydantic

# Set up environment
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Copy example structure
# (Copy files from examples/ directory in this repo)
```

### Phase 1: Author First Concept
1. Choose domain (microeconomics, programming, business, etc.)
2. Identify 5-7 concepts in sequence
3. Author concept-001 completely:
   - metadata.json
   - text-explainer.md
   - examples.json
   - dialogue-prompts.json
   - written-prompts.json
   - applied-tasks.json

### Phase 2: Build Backend
1. Implement resource loading tools
2. Implement learner model management
3. Integrate Claude API with tool use
4. Test agent conversation flow

### Phase 3: Build Frontend
1. Create simple chat UI
2. Build FastAPI backend
3. Connect frontend to backend
4. Add progress display

### Phase 4: Complete & Test
1. Author remaining concepts (002-007)
2. Implement progression logic
3. Self-test complete system
4. Pilot with 1-2 real learners
5. Iterate based on feedback

## Design Principles

### Mastery-Based Progression
No time limits. No arbitrary passing scores. Progress only when understanding is demonstrated consistently across multiple assessment types.

### Continuous Assessment
Every interaction provides evidence of understanding. Assessment and learning are inseparable.

### Transparency
AI always explains its decisions to learners. Progression, continuation, and regression are accompanied by clear rationale.

### Multi-Modal Evidence
Mastery requires demonstrating understanding through:
- Explanation (dialogue)
- Articulation (written)
- Application (applied tasks)

### Adaptive Sequencing Only (PoC)
Same resources for all learners, but personalized order and pacing. Future versions may add resource variation or dynamic content generation.

## Technology Stack (PoC)

**Backend**:
- Python + FastAPI
- Claude 3.5 Sonnet (Anthropic API)
- JSON file storage

**Frontend**:
- Simple HTML/CSS/JavaScript
- Chat interface
- Progress dashboard

**Future (Production)**:
- Database (PostgreSQL)
- User authentication
- Instructor dashboard
- Analytics engine

## Success Metrics

### Proof of Concept
- ✅ Agent successfully conducts continuous assessment
- ✅ Progression decisions are appropriate and well-justified
- ✅ At least 1 learner completes full path (5-7 concepts)
- ✅ Learner reports positive experience
- ✅ System demonstrates feasibility of approach

### Long-Term Vision
- Scales to multiple domains
- Serves 100+ concurrent learners
- Instructor tools for content authoring
- Analytics on agent performance
- Research publication on effectiveness

## What Makes This Different

### vs. Traditional Online Courses
- Not linear module progression
- Not periodic quizzes/exams
- Continuous, conversational assessment
- Dynamic sequencing, not fixed path

### vs. Existing Adaptive Learning
- Not just adjusting difficulty
- Not just hints and scaffolding
- Full learning path adaptation
- Regression to prerequisites when needed
- Multi-modal assessment, not just multiple choice

### vs. AI Tutors
- Not just Q&A chatbot
- Persistent learner model across sessions
- Systematic progression through curriculum
- Mastery-based advancement

## Future Directions

### After PoC Success
1. **Multi-Domain Expansion**: Additional subject areas
2. **Resource Variation**: Multiple formats (video vs text) based on learning style
3. **Dynamic Content**: AI-generated examples tailored to learner context
4. **Collaborative Learning**: Peer interaction while maintaining individual pacing
5. **Instructor Analytics**: Dashboard for monitoring and intervention
6. **Research**: Publish findings, compare to traditional instruction

### Research Questions
- What mastery thresholds optimize learning vs. time?
- How accurate are AI assessments vs. human expert evaluation?
- What's the ideal balance of assessment modalities?
- How does learner experience compare to traditional courses?
- Does mastery-based progression lead to better retention?

## Contributing

This is currently a planning/architecture project. Once PoC is built, we'll welcome:
- Concept authoring (domain expertise)
- Assessment rubric refinement
- Agent prompt engineering
- Frontend/backend development
- Testing and feedback

## License

TBD - likely MIT or Apache 2.0

## Contact

Project Lead: [Your Name]
Institution: Ivey Business School, EdTech Lab

---

## Project Structure

```
adaptive-learning-poc/
├── README.md                          # This file
├── ARCHITECTURE.md                    # System design document
├── IMPLEMENTATION-ROADMAP.md          # Build guide
├── resource-bank/
│   ├── concepts/
│   │   ├── concept-001/
│   │   │   ├── metadata.json
│   │   │   ├── resources/
│   │   │   │   ├── text-explainer.md
│   │   │   │   ├── video-lecture.mp4
│   │   │   │   └── examples.json
│   │   │   └── assessments/
│   │   │       ├── dialogue-prompts.json
│   │   │       ├── written-prompts.json
│   │   │       └── applied-tasks.json
│   │   └── concept-002/...
│   └── learning-paths/
│       └── default-sequence.json
├── prompts/
│   └── tutor-agent-system-prompt.md
├── learner-models/
│   └── learner-001.json
├── backend/
│   ├── main.py                        # FastAPI app
│   ├── agent.py                       # AI agent logic
│   └── tools.py                       # Resource loading, learner model
├── frontend/
│   └── index.html                     # Chat UI
└── logs/
    └── interactions.log               # For debugging and analysis
```

---

**Last Updated**: 2025-10-21
**Version**: 0.1.0 (Planning)
