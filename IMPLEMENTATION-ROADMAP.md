# Implementation Roadmap: Adaptive Self-Paced Learning System
## Proof of Concept (6-8 Weeks)

**Version**: 0.1.0
**Target**: Minimal viable system for 1-2 pilot learners
**Last Updated**: 2025-10-21

---

## Overview

This roadmap breaks down the PoC implementation into 4 phases over 6-8 weeks. Each phase builds on the previous, allowing for incremental validation and learning.

**Success Criteria**: Complete one learner journey (5-7 concepts) with demonstrated continuous assessment, appropriate progression/regression decisions, and positive learner experience.

---

## Phase 1: Foundation (Week 1-2)

**Goal**: Set up development environment and create first concept's complete resource set

### Tasks

#### 1.1 Environment Setup (2-3 hours)
- [ ] Create project repository
- [ ] Set up Python environment (Python 3.10+)
  ```bash
  python -m venv venv
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  pip install anthropic fastapi uvicorn python-dotenv pydantic
  ```
- [ ] Get Anthropic API key (https://console.anthropic.com/)
- [ ] Create `.env` file:
  ```
  ANTHROPIC_API_KEY=your_key_here
  ```
- [ ] Create basic directory structure:
  ```
  project/
  ├── resource-bank/
  │   └── concepts/
  ├── prompts/
  ├── learner-models/
  ├── backend/
  │   ├── main.py
  │   ├── agent.py
  │   └── tools.py
  ├── frontend/
  │   └── index.html
  └── logs/
  ```

#### 1.2 Choose Domain and Concept Sequence (3-4 hours)
- [ ] Select domain for PoC (recommendation: microeconomics, Python programming basics, or business fundamentals)
- [ ] Identify 5-7 concepts in logical sequence
- [ ] Map prerequisite relationships
- [ ] Create `learning-paths/default-sequence.json`

**Example concept sequence (microeconomics)**:
1. Supply and Demand Fundamentals
2. Market Equilibrium
3. Elasticity
4. Consumer and Producer Surplus
5. Market Efficiency
6. Government Intervention (Price Controls)
7. Taxes and Subsidies

#### 1.3 Author First Concept Resources (8-12 hours)
- [ ] Create `concept-001/` directory structure
- [ ] Write `metadata.json`
- [ ] Author `resources/text-explainer.md` (1000-1500 words)
- [ ] Create `resources/examples.json` (3-5 worked examples)
- [ ] Find/create video resource (or create transcript for future video)
- [ ] Write `assessments/dialogue-prompts.json` (4-5 prompts with rubrics)
- [ ] Write `assessments/written-prompts.json` (2 prompts with rubrics)
- [ ] Write `assessments/applied-tasks.json` (2-3 tasks with rubrics)

**Quality Check**:
- All learning objectives are assessable
- Rubrics are specific and actionable
- Examples cover common misconceptions
- Difficulty progression is clear

#### 1.4 Test Resource Completeness (1-2 hours)
- [ ] Read through resources as if you're a learner
- [ ] Attempt all assessment prompts yourself
- [ ] Verify rubrics accurately capture quality levels
- [ ] Refine based on self-testing

**Deliverable**: Concept-001 fully authored and validated

---

## Phase 2: Backend Core (Week 2-3)

**Goal**: Build AI agent with tool use and basic orchestration logic

### Tasks

#### 2.1 Implement Resource Loading Tools (4-6 hours)

Create `backend/tools.py`:

```python
import json
from pathlib import Path

RESOURCE_BANK_PATH = Path("resource-bank/concepts")

def load_resource(concept_id: str, resource_type: str) -> dict:
    """Load a resource from the resource bank."""
    resource_path = RESOURCE_BANK_PATH / concept_id / "resources" / f"{resource_type}.md"
    if resource_type == "examples":
        resource_path = RESOURCE_BANK_PATH / concept_id / "resources" / "examples.json"

    if not resource_path.exists():
        return {"error": f"Resource not found: {resource_path}"}

    if resource_path.suffix == ".json":
        with open(resource_path) as f:
            return json.load(f)
    else:
        with open(resource_path) as f:
            return {"content": f.read()}

def load_assessment(concept_id: str, assessment_type: str) -> dict:
    """Load assessment prompts for a concept."""
    assessment_path = RESOURCE_BANK_PATH / concept_id / "assessments" / f"{assessment_type}-prompts.json"

    if not assessment_path.exists():
        return {"error": f"Assessment not found: {assessment_path}"}

    with open(assessment_path) as f:
        return json.load(f)

def load_concept_metadata(concept_id: str) -> dict:
    """Load concept metadata."""
    metadata_path = RESOURCE_BANK_PATH / concept_id / "metadata.json"

    if not metadata_path.exists():
        return {"error": f"Metadata not found: {metadata_path}"}

    with open(metadata_path) as f:
        return json.load(f)
```

- [ ] Implement `load_resource()`
- [ ] Implement `load_assessment()`
- [ ] Implement `load_concept_metadata()`
- [ ] Test each function with concept-001
- [ ] Add error handling

#### 2.2 Implement Learner Model Management (4-6 hours)

Add to `backend/tools.py`:

```python
def create_learner_model(learner_id: str) -> dict:
    """Create a new learner model."""
    model = {
        "learner_id": learner_id,
        "current_concept": None,
        "learning_path_progress": [],
        "concept_mastery": {},
        "overall_progress": 0.0,
        "session_history": []
    }
    save_learner_model(learner_id, model)
    return model

def load_learner_model(learner_id: str) -> dict:
    """Load learner model from disk."""
    model_path = Path("learner-models") / f"{learner_id}.json"

    if not model_path.exists():
        return create_learner_model(learner_id)

    with open(model_path) as f:
        return json.load(f)

def save_learner_model(learner_id: str, model: dict):
    """Save learner model to disk."""
    model_path = Path("learner-models") / f"{learner_id}.json"
    model_path.parent.mkdir(exist_ok=True)

    with open(model_path, "w") as f:
        json.dump(model, f, indent=2)

def update_learner_model(learner_id: str, concept_id: str, assessment_data: dict) -> dict:
    """Update learner model with new assessment data."""
    model = load_learner_model(learner_id)

    # Initialize concept if not exists
    if concept_id not in model["concept_mastery"]:
        model["concept_mastery"][concept_id] = {
            "status": "in_progress",
            "confidence": 0.0,
            "attempts": 0,
            "assessment_scores": {}
        }

    # Update assessment scores
    concept = model["concept_mastery"][concept_id]
    assessment_type = assessment_data["type"]

    if assessment_type not in concept["assessment_scores"]:
        concept["assessment_scores"][assessment_type] = {
            "average_score": 0.0,
            "attempts": 0,
            "assessments": []
        }

    # Add new assessment
    concept["assessment_scores"][assessment_type]["assessments"].append(assessment_data)
    concept["assessment_scores"][assessment_type]["attempts"] += 1

    # Recalculate average
    scores = [a["score"] for a in concept["assessment_scores"][assessment_type]["assessments"]]
    concept["assessment_scores"][assessment_type]["average_score"] = sum(scores) / len(scores)

    # Recalculate overall confidence
    concept["confidence"] = calculate_mastery(learner_id, concept_id)
    concept["attempts"] += 1

    save_learner_model(learner_id, model)
    return model

def calculate_mastery(learner_id: str, concept_id: str) -> float:
    """Calculate overall mastery confidence for a concept."""
    model = load_learner_model(learner_id)

    if concept_id not in model["concept_mastery"]:
        return 0.0

    concept = model["concept_mastery"][concept_id]
    scores = concept["assessment_scores"]

    # Average across all assessment types that have been attempted
    type_averages = [scores[t]["average_score"] for t in scores if scores[t]["attempts"] > 0]

    if not type_averages:
        return 0.0

    return sum(type_averages) / len(type_averages)
```

- [ ] Implement learner model CRUD operations
- [ ] Implement confidence calculation logic
- [ ] Test with sample assessment data
- [ ] Verify JSON files are created correctly

#### 2.3 Implement AI Agent Core (8-10 hours)

Create `backend/agent.py`:

```python
import anthropic
import os
from typing import List, Dict
from tools import *

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load system prompt
with open("prompts/tutor-agent-system-prompt.md") as f:
    SYSTEM_PROMPT = f.read()

def create_tool_definitions() -> List[Dict]:
    """Define tools available to the agent."""
    return [
        {
            "name": "load_resource",
            "description": "Load a learning resource (text, examples) from the resource bank",
            "input_schema": {
                "type": "object",
                "properties": {
                    "concept_id": {"type": "string", "description": "Concept ID (e.g., 'concept-001')"},
                    "resource_type": {"type": "string", "enum": ["text-explainer", "examples"]}
                },
                "required": ["concept_id", "resource_type"]
            }
        },
        {
            "name": "load_assessment",
            "description": "Load assessment prompts for a concept",
            "input_schema": {
                "type": "object",
                "properties": {
                    "concept_id": {"type": "string"},
                    "assessment_type": {"type": "string", "enum": ["dialogue", "written", "applied"]}
                },
                "required": ["concept_id", "assessment_type"]
            }
        },
        {
            "name": "update_learner_model",
            "description": "Update learner progress with assessment results",
            "input_schema": {
                "type": "object",
                "properties": {
                    "learner_id": {"type": "string"},
                    "concept_id": {"type": "string"},
                    "assessment_data": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "score": {"type": "number"},
                            "feedback": {"type": "string"}
                        }
                    }
                },
                "required": ["learner_id", "concept_id", "assessment_data"]
            }
        },
        {
            "name": "calculate_mastery",
            "description": "Calculate current mastery confidence for a concept",
            "input_schema": {
                "type": "object",
                "properties": {
                    "learner_id": {"type": "string"},
                    "concept_id": {"type": "string"}
                },
                "required": ["learner_id", "concept_id"]
            }
        }
    ]

def process_tool_call(tool_name: str, tool_input: dict):
    """Execute tool calls from the agent."""
    if tool_name == "load_resource":
        return load_resource(tool_input["concept_id"], tool_input["resource_type"])
    elif tool_name == "load_assessment":
        return load_assessment(tool_input["concept_id"], tool_input["assessment_type"])
    elif tool_name == "update_learner_model":
        return update_learner_model(
            tool_input["learner_id"],
            tool_input["concept_id"],
            tool_input["assessment_data"]
        )
    elif tool_name == "calculate_mastery":
        confidence = calculate_mastery(tool_input["learner_id"], tool_input["concept_id"])
        return {"confidence": confidence}
    else:
        return {"error": f"Unknown tool: {tool_name}"}

def chat(learner_id: str, user_message: str, conversation_history: List[Dict]) -> tuple:
    """Send message to tutor agent and get response."""

    # Load learner context
    learner_model = load_learner_model(learner_id)

    # Add learner context to system prompt
    context = f"\n\n## Current Learner Context\n\n{json.dumps(learner_model, indent=2)}"
    full_system_prompt = SYSTEM_PROMPT + context

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Call Claude with tool use
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=full_system_prompt,
        tools=create_tool_definitions(),
        messages=conversation_history
    )

    # Process tool uses
    while response.stop_reason == "tool_use":
        # Extract tool uses
        tool_uses = [block for block in response.content if block.type == "tool_use"]

        # Add assistant response to history
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        # Execute tools and collect results
        tool_results = []
        for tool_use in tool_uses:
            result = process_tool_call(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result)
            })

        # Add tool results to history
        conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # Continue conversation
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=full_system_prompt,
            tools=create_tool_definitions(),
            messages=conversation_history
        )

    # Extract final text response
    text_response = ""
    for block in response.content:
        if hasattr(block, "text"):
            text_response += block.text

    # Add final assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": response.content
    })

    return text_response, conversation_history
```

- [ ] Implement Claude API integration
- [ ] Implement tool use handling
- [ ] Test with simple conversation
- [ ] Verify tool calls execute correctly
- [ ] Test learner model updates

#### 2.4 Test Backend End-to-End (3-4 hours)
- [ ] Create test script that simulates learner conversation
- [ ] Verify agent loads resources correctly
- [ ] Verify agent assesses responses and updates learner model
- [ ] Check that confidence scores are calculated correctly
- [ ] Debug any issues

**Deliverable**: Functional backend with AI agent that can conduct assessment dialogue

---

## Phase 3: Frontend & Integration (Week 3-4)

**Goal**: Create simple web interface and connect to backend

### Tasks

#### 3.1 Build Simple Chat UI (4-6 hours)

Create `frontend/index.html`:

- [ ] Basic HTML structure with chat window
- [ ] Message display area (scrollable)
- [ ] Text input field
- [ ] Send button
- [ ] Simple CSS styling
- [ ] JavaScript for sending/receiving messages

**Minimal features**:
- Display conversation history
- Send user messages to backend
- Display agent responses
- Show typing indicator while waiting

#### 3.2 Create FastAPI Backend (3-4 hours)

Create `backend/main.py`:

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import agent

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation histories (in-memory for PoC)
conversations = {}

class ChatMessage(BaseModel):
    learner_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    confidence: float
    current_concept: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_msg: ChatMessage):
    """Process chat message from learner."""

    # Initialize conversation if new learner
    if chat_msg.learner_id not in conversations:
        conversations[chat_msg.learner_id] = []

    # Get response from agent
    response_text, updated_history = agent.chat(
        chat_msg.learner_id,
        chat_msg.message,
        conversations[chat_msg.learner_id]
    )

    # Update stored history
    conversations[chat_msg.learner_id] = updated_history

    # Get current learner state
    learner_model = agent.load_learner_model(chat_msg.learner_id)
    current_concept = learner_model.get("current_concept", "Not started")

    # Get confidence if concept in progress
    confidence = 0.0
    if current_concept and current_concept in learner_model.get("concept_mastery", {}):
        confidence = learner_model["concept_mastery"][current_concept].get("confidence", 0.0)

    return ChatResponse(
        response=response_text,
        confidence=confidence,
        current_concept=current_concept
    )

@app.get("/progress/{learner_id}")
async def get_progress(learner_id: str):
    """Get learner's current progress."""
    learner_model = agent.load_learner_model(learner_id)
    return learner_model

# Serve frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

- [ ] Implement `/chat` endpoint
- [ ] Implement `/progress` endpoint
- [ ] Test with Postman or curl
- [ ] Verify CORS settings

#### 3.3 Connect Frontend to Backend (2-3 hours)
- [ ] Add fetch() calls from JavaScript to backend API
- [ ] Handle responses and update UI
- [ ] Display errors gracefully
- [ ] Test full flow: type message → send → receive response

#### 3.4 Add Progress Display (2-3 hours)
- [ ] Show current concept name
- [ ] Show confidence score (progress bar or percentage)
- [ ] Show number of concepts mastered
- [ ] Update in real-time as conversation progresses

**Deliverable**: Functional web interface for learner interaction

---

## Phase 4: Content Completion & Testing (Week 5-6)

**Goal**: Complete resource authoring and conduct pilot testing

### Tasks

#### 4.1 Author Remaining Concepts (16-24 hours)
- [ ] Create concept-002 through concept-007
- [ ] For each concept:
  - [ ] metadata.json
  - [ ] text-explainer.md
  - [ ] examples.json
  - [ ] dialogue-prompts.json (4-5 prompts)
  - [ ] written-prompts.json (2 prompts)
  - [ ] applied-tasks.json (2-3 tasks)
- [ ] Quality check each concept

**Time-saving tips**:
- Reuse rubric structures across concepts
- Use LLM assistance to draft initial content (but review carefully!)
- Focus on quality over quantity - better to have 5 excellent concepts than 7 mediocre ones

#### 4.2 Implement Progression Logic (4-6 hours)
- [ ] Create `learning-paths/default-sequence.json`
- [ ] Implement `get_next_concept()` in tools.py
- [ ] Implement progression decision in agent
- [ ] Test progression between concepts
- [ ] Test regression (manually trigger low confidence scenario)

#### 4.3 Self-Test Complete System (4-6 hours)
- [ ] Go through entire learning path yourself
- [ ] Deliberately give wrong answers to test assessment
- [ ] Give partially correct answers to test feedback quality
- [ ] Verify progression happens at appropriate times
- [ ] Document any issues or improvements needed

#### 4.4 Pilot User Testing (8-12 hours)
- [ ] Recruit 1-2 pilot learners
- [ ] Brief them on the system (but don't over-explain)
- [ ] Observe them using the system (take notes)
- [ ] Ask them to think aloud
- [ ] Collect feedback after completion
- [ ] Analyze:
  - Where did agent make good decisions?
  - Where did agent make poor decisions?
  - What was the learner experience like?
  - How long did it take?

#### 4.5 Iteration Based on Feedback (4-8 hours)
- [ ] Refine assessment rubrics based on observed agent decisions
- [ ] Improve feedback quality
- [ ] Adjust mastery thresholds if needed
- [ ] Fix any bugs discovered
- [ ] Update documentation

**Deliverable**: Validated PoC with 1-2 successful learner completions

---

## Phase 5: Documentation & Next Steps (Week 7-8)

**Goal**: Document learnings and plan production system

### Tasks

#### 5.1 Analysis & Documentation (6-8 hours)
- [ ] Analyze logged interactions
- [ ] Calculate metrics:
  - Time to complete full learning path
  - Number of assessments per concept
  - Progression vs. regression rate
  - Agent decision accuracy (review manually)
- [ ] Document findings in `POC-RESULTS.md`
- [ ] Identify what worked well
- [ ] Identify what needs improvement

#### 5.2 Code Documentation (3-4 hours)
- [ ] Add docstrings to all functions
- [ ] Create `README.md` with setup instructions
- [ ] Document API endpoints
- [ ] Create `CONTRIBUTING.md` for future contributors

#### 5.3 Plan Production System (4-6 hours)
- [ ] Design database schema (replace JSON files)
- [ ] Plan user authentication system
- [ ] Design instructor dashboard features
- [ ] Plan analytics and reporting
- [ ] Estimate timeline for production build
- [ ] Create `PRODUCTION-ROADMAP.md`

---

## Resource Estimates

### Time Commitment
- **Weeks 1-2**: 15-20 hours (authoring-heavy)
- **Weeks 3-4**: 15-20 hours (development-heavy)
- **Weeks 5-6**: 25-30 hours (authoring + testing)
- **Weeks 7-8**: 10-15 hours (documentation + planning)
- **Total**: 65-85 hours over 6-8 weeks

### Cost Estimates (API Usage)
- Claude 3.5 Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Estimated usage for 1-2 pilot learners: $5-15 total
- Budget $50 for safety margin during development/testing

---

## Risk Mitigation

### Risk: Resource authoring takes longer than expected
**Mitigation**: Start with 3-4 concepts instead of 7. Validate core system first, add concepts later.

### Risk: AI agent makes poor assessment decisions
**Mitigation**: Log all decisions with rationale. Review manually and refine rubrics iteratively.

### Risk: Learners find experience frustrating
**Mitigation**: Include "help" mechanism. Allow learners to request hints. Tune feedback to be more encouraging.

### Risk: Technical implementation challenges
**Mitigation**: Use proven tools (FastAPI, Claude API). Start simple, add complexity gradually.

---

## Success Criteria

### Must Have (Minimum Viable)
- ✅ Agent can introduce concepts and provide resources
- ✅ Agent can assess understanding across 3 modalities
- ✅ Agent can calculate mastery confidence scores
- ✅ Agent can progress learner when ready
- ✅ At least 1 learner completes full path (3+ concepts)
- ✅ Learner model persists across sessions

### Should Have (Desired)
- Agent can identify gaps and provide targeted support
- Agent can regress to prerequisites when needed
- Learner reports positive experience
- Agent decisions align with manual expert review (80%+ agreement)

### Nice to Have (Bonus)
- Agent generates custom examples based on learner interests
- Multiple assessment difficulty levels per concept
- Detailed analytics on learner progress

---

## Next Steps After PoC

If PoC is successful:

1. **Expand Content**: Add more concepts and domains
2. **Multi-User Support**: Build database and authentication
3. **Instructor Tools**: Dashboard for monitoring, resource authoring
4. **Analytics**: Track agent performance, A/B test rubrics
5. **Scalability**: Optimize for 100+ concurrent learners
6. **Research**: Publish findings on AI-driven adaptive learning

If PoC reveals challenges:

1. **Pivot on Assessment**: May need more structured assessment formats
2. **Pivot on Sequencing**: May need hybrid (some linear, some adaptive)
3. **Pivot on Scope**: May need to narrow domain or simplify progression logic

---

## Appendix: Tool Alternatives

### If you prefer different tech stack:

**Backend Alternatives**:
- Node.js + Express instead of Python + FastAPI
- Use OpenAI GPT-4 instead of Claude (adjust prompts)

**Frontend Alternatives**:
- React or Vue.js instead of vanilla JavaScript
- Mobile app (React Native) instead of web

**Storage Alternatives**:
- SQLite database instead of JSON files (better for multi-user)
- PostgreSQL for production

**Deployment Alternatives**:
- Vercel/Netlify for frontend
- Railway/Render for backend
- AWS/Google Cloud for production

The core concepts (resource bank, AI agent, learner model, assessment) remain the same regardless of implementation technology.
