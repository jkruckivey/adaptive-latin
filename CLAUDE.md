# CLAUDE.md - AI Assistant Guide for Adaptive Latin Learning System

**Version:** 1.1.0
**Last Updated:** 2025-11-19
**Repository:** adaptive-latin

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Structure](#codebase-structure)
3. [Technology Stack](#technology-stack)
4. [Key Architecture Components](#key-architecture-components)
5. [Development Workflows](#development-workflows)
6. [Testing and Deployment](#testing-and-deployment)
7. [Coding Conventions](#coding-conventions)
8. [Common Tasks](#common-tasks)
9. [Key Files Reference](#key-files-reference)
10. [Adding New Features](#adding-new-features)

---

## Project Overview

### Purpose
An innovative adaptive learning platform that uses AI (Anthropic's Claude) to continuously assess learners and dynamically sequence content for mastery-based progression. The system implements a **domain-agnostic framework** currently deployed for teaching Latin grammar.

### Core Innovation
Unlike traditional adaptive learning that adjusts difficulty or provides hints, this system **adjusts the learning path itself** - deciding what concept comes next (or whether to review a previous one) based on continuous assessment of understanding.

### Key Features
- **Continuous Assessment**: Every interaction provides evidence of understanding
- **Mastery-Based Progression**: Advance only when ready (≥0.85 confidence)
- **Multi-Modal Assessment**: Dialogue, written, and applied tasks
- **Confidence Tracking**: Metacognitive calibration through self-assessment
- **Adaptive Sequencing**: Personalized order and pacing
- **Course Creation**: User-generated content system with wizard interface
- **Spaced Repetition**: Review scheduling for retention

### Current Status
**Version**: 0.3.0 (Released 2025-11-01)
**Domain**: Latin Grammar (7 concepts) + User-generated courses
**Stage**: Production-ready with advanced course creation and pedagogical features

**Recent Updates**:
- Modular backend architecture with dedicated routers
- Teaching Moment assessment type for interactive misconception correction
- OnboardingQuestionBuilder for course creation wizard
- Pedagogical tools for contextualized content generation
- Enhanced assessment builder with AI generation capabilities

---

## Codebase Structure

```
adaptive-latin/
├── backend/                         # FastAPI Python backend (~7,500 lines total)
│   ├── app/
│   │   ├── main.py                 # FastAPI application setup and middleware
│   │   ├── agent.py                # Core Claude AI integration with tool use
│   │   ├── tools.py                # Resource loading and learner model management
│   │   ├── routers/                # Modular API routers (NEW architecture)
│   │   │   ├── chat.py            # Chat and conversation endpoints (~6.5k lines)
│   │   │   ├── concepts.py        # Concept management endpoints (~1.8k lines)
│   │   │   ├── content.py         # Content generation and retrieval (~22k lines)
│   │   │   ├── conversations.py   # Conversation history endpoints (~6.7k lines)
│   │   │   ├── courses.py         # Course management endpoints (~16k lines)
│   │   │   ├── learner.py         # Individual learner endpoints (~8.9k lines)
│   │   │   └── learners.py        # Learner collection endpoints (~11.8k lines)
│   │   ├── pedagogical_tools.py   # Contextualized content generation (NEW)
│   │   ├── confidence.py          # Confidence tracking and calibration
│   │   ├── content_generators.py  # Dynamic content generation
│   │   ├── conversations.py       # Conversation state management
│   │   ├── cartridge_parser.py    # Common Cartridge import/export
│   │   ├── config.py              # Configuration management
│   │   ├── constants.py           # Application constants (NEW)
│   │   ├── database.py            # Database abstraction layer
│   │   ├── auth.py                # JWT authentication
│   │   ├── schemas.py             # Pydantic data models
│   │   ├── spaced_repetition.py   # Review scheduling algorithm
│   │   ├── content_cache.py       # Content caching system
│   │   ├── smart_content_retrieval.py # Smart content selection
│   │   ├── source_extraction.py   # PDF/external source parsing
│   │   ├── tutor_agent.py         # Tutor-specific agent logic
│   │   ├── roman_agent.py         # Roman persona agent
│   │   └── stone_inscription.py   # Latin text rendering
│   ├── data/
│   │   └── learner-models/        # JSON files for learner progress
│   ├── prompts/                   # AI agent system prompts
│   ├── tests/                     # Backend tests
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment variable template
│   └── README.md                 # Backend documentation
│
├── frontend/                       # React + Vite frontend (~15k lines total)
│   ├── src/
│   │   ├── App.jsx               # Main application component (163 lines)
│   │   ├── api.js                # API client functions
│   │   ├── components/
│   │   │   ├── content-types/    # Content display components
│   │   │   │   ├── AssessmentResult.jsx
│   │   │   │   ├── DialogueQuestion.jsx
│   │   │   │   ├── ExampleSet.jsx
│   │   │   │   ├── FillBlank.jsx
│   │   │   │   ├── LessonView.jsx
│   │   │   │   ├── MultipleChoice.jsx
│   │   │   │   ├── ParadigmTable.jsx
│   │   │   │   ├── SentenceDiagram.jsx
│   │   │   │   ├── SimulationViewer.jsx
│   │   │   │   └── TeachingMoment.jsx  # Interactive misconception correction (NEW)
│   │   │   ├── course-creation/  # Course creation wizard
│   │   │   │   ├── ActionVerbHelper.jsx
│   │   │   │   ├── AssessmentBuilder.jsx  # AI-powered assessment generation (NEW)
│   │   │   │   ├── ComprehensionQuizBuilder.jsx
│   │   │   │   ├── ConceptEditor.jsx
│   │   │   │   ├── ConceptPlanner.jsx
│   │   │   │   ├── CourseCreationWizard.jsx
│   │   │   │   ├── CourseReview.jsx
│   │   │   │   ├── CourseSetup.jsx
│   │   │   │   ├── CurriculumRoadmap.jsx
│   │   │   │   ├── LearningOutcomeBuilder.jsx
│   │   │   │   ├── LearningOutcomeGenerator.jsx
│   │   │   │   ├── ModulePlanner.jsx
│   │   │   │   ├── OnboardingQuestionBuilder.jsx  # Learner profiling questions (NEW)
│   │   │   │   ├── ResourceLibrary.jsx
│   │   │   │   └── TaxonomySelector.jsx
│   │   │   ├── learner/          # Learner-facing components (NEW)
│   │   │   │   ├── ComprehensionQuiz.jsx
│   │   │   │   ├── DiscussionPrompt.jsx
│   │   │   │   ├── RequiredMaterialsGate.jsx
│   │   │   │   └── SelfAttestation.jsx
│   │   │   ├── admin/            # Admin components (NEW)
│   │   │   │   ├── AdminDashboard.jsx
│   │   │   │   ├── CourseEditor.jsx
│   │   │   │   └── UserInsights.jsx
│   │   │   ├── widgets/          # Interactive widgets (NEW)
│   │   │   │   ├── DeclensionExplorer.jsx
│   │   │   │   ├── ScenarioWidget.jsx
│   │   │   │   └── WordOrderManipulator.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── ConceptMasteryModal.jsx
│   │   │   ├── ConfidenceRating.jsx
│   │   │   ├── ConfidenceSlider.jsx
│   │   │   ├── ContentRenderer.jsx
│   │   │   ├── CourseSelector.jsx
│   │   │   ├── ExternalResources.jsx
│   │   │   ├── FloatingTutorButton.jsx
│   │   │   ├── LandingPage.jsx
│   │   │   ├── LearnerProfileReport.jsx
│   │   │   ├── MasteryProgressBar.jsx
│   │   │   ├── OnboardingFlow.jsx
│   │   │   ├── ProgressDashboard.jsx
│   │   │   ├── RomanChat.jsx      # Roman persona chat
│   │   │   ├── SkeletonLoader.jsx # Loading states (NEW)
│   │   │   ├── Syllabus.jsx       # Course syllabus view
│   │   │   └── TutorChat.jsx      # Main chat interface
│   │   ├── hooks/                # Custom React hooks
│   │   └── utils/                # Utility functions
│   ├── package.json              # Node dependencies
│   └── vite.config.js           # Vite configuration
│
├── resource-bank/                 # Learning content repository
│   ├── latin-grammar/            # Official Latin course (7 concepts)
│   │   ├── concept-001/          # First Declension + Sum
│   │   │   ├── metadata.json     # Concept metadata
│   │   │   ├── resources/        # Teaching materials
│   │   │   │   ├── text-explainer.md
│   │   │   │   └── examples.json
│   │   │   └── assessments/      # Assessment prompts
│   │   │       ├── dialogue-prompts.json
│   │   │       ├── written-prompts.json
│   │   │       └── applied-tasks.json
│   │   └── concept-002/ ... concept-007/
│   ├── user-courses/             # User-generated courses
│   │   └── fundamentals-of-excel-and-analytics/
│   └── external-resources.json   # External content references
│
├── .claude/                       # Claude CLI configuration
│   ├── settings.local.json       # Local development settings
│   └── skills/                   # Custom skills
│       ├── canvas-design/        # Visual design skill
│       └── webapp-testing/       # Browser testing skill
│
├── examples/                      # Example resources and templates
├── screenshots/                   # UI screenshots
├── ARCHITECTURE.md               # System architecture documentation
├── COURSE_CREATION_REQUIREMENTS.md # Course creation specs
├── IMPLEMENTATION-ROADMAP.md     # Development roadmap
├── CHANGELOG.md                  # Version history
├── STATUS.md                     # Current project status
├── render.yaml                   # Render deployment config
└── .gitignore                    # Git ignore rules
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109.0 (async, REST API with modular routers)
- **AI Model**: Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **AI SDK**: anthropic >= 0.71.0
- **Language**: Python 3.11+
- **Data Storage**:
  - JSON files (learner models, courses)
  - SQLite (content cache, conversations)
- **Authentication**: JWT with OAuth2 bearer tokens
- **Validation**: Pydantic >= 2.5.3
- **CORS**: FastAPI-CORS 0.0.6
- **Rate Limiting**: SlowAPI 0.1.9
- **PDF Processing**: pdfplumber 0.11.0
- **HTTP Requests**: requests 2.31.0
- **Server**: Uvicorn[standard] 0.27.0

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 6.0.7
- **Router**: react-router-dom 7.9.6
- **Styling**: CSS (component-scoped)
- **Markdown**: react-markdown 9.0.1
- **Animations**: canvas-confetti 1.9.4 (celebration effects)
- **HTTP Client**: Fetch API (wrapped in api.js)

### Development Tools
- **Version Control**: Git
- **Deployment**: Render.com (auto-deploy from git)
- **Testing**: pytest (backend)
- **Code Quality**: Python logging, error handling with try-catch

### AI Integration
- **Primary**: Anthropic Claude API with tool use
- **Capabilities**:
  - Resource loading (text, examples, assessments)
  - Learner model management
  - Mastery calculation
  - Content generation
  - Confidence calibration

---

## Key Architecture Components

### 1. AI Agent System (`backend/app/agent.py`)

**Purpose**: Orchestrates the learning experience using Claude AI

**Key Functions**:
- `run_agent(learner_id, message, conversation_history, course_id)` - Main conversation handler
- Tool definitions for Claude:
  - `load_resource` - Fetch teaching materials
  - `load_assessment` - Get assessment prompts
  - `load_concept_metadata` - Get concept info
  - `track_confidence` - Calculate calibration
  - `update_learner_model` - Record assessment results
  - `calculate_mastery` - Check if mastery criteria met
  - `get_next_concept` - Determine progression

**System Prompt**: Loaded from `backend/prompts/tutor-agent-system-prompt-active.md`

### 2. Resource Bank (`resource-bank/`)

**Structure**: Pre-authored learning materials organized by concepts

**Concept Directory Layout**:
```
concept-XXX/
├── metadata.json          # Prerequisites, objectives, vocabulary
├── resources/
│   ├── text-explainer.md  # Main teaching content (200-500 lines)
│   └── examples.json      # Structured examples
└── assessments/
    ├── dialogue-prompts.json    # Socratic questions with rubrics
    ├── written-prompts.json     # Essay/reflection prompts
    └── applied-tasks.json       # Practice exercises
```

**Metadata Schema**:
```json
{
  "id": "concept-001",
  "title": "First Declension Nouns + Sum, esse (present)",
  "domain": "latin-grammar",
  "difficulty": 1,
  "prerequisites": [],
  "learning_objectives": ["..."],
  "estimated_mastery_time": "60-90 minutes",
  "vocabulary": [...]
}
```

### 3. Learner Model (`backend/data/learner-models/`)

**Purpose**: Persistent tracking of learner knowledge and progress

**Schema**:
```json
{
  "learner_id": "user_123",
  "created_at": "2025-10-21T12:00:00",
  "current_concept": "concept-002",
  "concepts": {
    "concept-001": {
      "status": "completed",
      "assessments": [...],
      "confidence_history": [...],
      "mastery_score": 0.88
    }
  },
  "overall_progress": {...},
  "spaced_repetition": {...}
}
```

**Mastery Criteria**:
- Overall confidence ≥ 0.85
- Minimum 3 assessments completed
- Consistency across assessment types

### 4. Modular Router Architecture (`backend/app/routers/`)

**Purpose**: Organized, maintainable API structure with separation of concerns

**Router Files**:
- `chat.py` - Chat and conversation endpoints
  - `/chat` - Main tutor conversation
  - `/tutor/start` - Initialize tutor session
  - `/tutor/continue` - Continue tutor conversation
  - `/roman/start` - Roman persona chat
  - `/scenarios` - List available scenarios

- `concepts.py` - Concept management
  - `/concepts` - List all concepts
  - `/concept/{concept_id}` - Get concept details

- `content.py` - Content generation and retrieval
  - `/generate-question` - AI question generation
  - `/generate-scenario` - AI scenario generation
  - Content caching integration

- `conversations.py` - Conversation history
  - `/conversations/recent` - Get recent conversations
  - `/conversations/struggle-detection` - Detect struggle patterns

- `courses.py` - Course management
  - `/courses` - Create/list courses
  - `/courses/{course_id}` - Get/update course
  - `/courses/{course_id}/import-cc` - Import Common Cartridge

- `learner.py` - Individual learner operations
  - `/start` - Initialize learner
  - `/progress/{learner_id}` - Get progress
  - `/mastery/{learner_id}/{concept_id}` - Check mastery

- `learners.py` - Learner collection operations
  - `/learners` - List all learners
  - `/learners/batch` - Batch operations

**Benefits**:
- Clear separation of concerns
- Easier testing and maintenance
- Better code organization
- Independent development of features

### 5. Pedagogical Tools (`backend/app/pedagogical_tools.py`)

**Purpose**: Domain-agnostic AI-powered content personalization

**Key Functions**:
- `generate_contextualized_example()` - Create examples tailored to learner interests
- `generate_analogy()` - Build conceptual bridges using familiar domains
- `generate_scaffolded_question()` - Adaptive difficulty questions
- `detect_misconception()` - Identify common misunderstandings

**Integration**: Used by tutor agent to personalize learning experiences

### 6. Assessment System

**Four Modalities**:

1. **Dialogue** (`dialogue-prompts.json`): Conversational Socratic questions
   - AI grades free-text responses using rubrics
   - Difficulty levels: basic, intermediate, advanced

2. **Written** (`written-prompts.json`): Extended response questions
   - Multi-dimensional rubrics (accuracy, clarity, examples)
   - Weighted scoring

3. **Applied** (`applied-tasks.json`): Practical exercises
   - Translation, problem-solving, case studies
   - Clear correct/incorrect answers

4. **Teaching Moment** (NEW): Interactive misconception correction
   - Real-time feedback on specific errors
   - Guided correction with hints
   - Prevents reinforcement of incorrect understanding

### 7. Progression Logic

**Decision Rules**:
```
After Each Assessment:
├─ confidence ≥ 0.85 AND 3+ assessments
│  └─ PROGRESS to next concept
├─ confidence 0.70-0.84
│  └─ CONTINUE current concept (targeted support)
└─ confidence < 0.70 after 2+ attempts
   └─ REGRESS to prerequisite or provide remediation
```

### 8. Course Creation System

**Wizard Components** (`frontend/src/components/course-creation/`):
- `CourseSetup.jsx` - Step 1: Basic course info
- `ModulePlanner.jsx` - Step 2: Outline modules
- `ConceptPlanner.jsx` - Plan individual concepts
- `LearningOutcomeBuilder.jsx` - Step 3: Define learning objectives
- `OnboardingQuestionBuilder.jsx` - Create learner profiling questions (NEW)
- `AssessmentBuilder.jsx` - AI-powered assessment generation with Bloom's taxonomy (NEW)
- `ComprehensionQuizBuilder.jsx` - Step 4: Create comprehension assessments
- `ResourceLibrary.jsx` - Manage course resources
- `CurriculumRoadmap.jsx` - Visualization of course structure
- `CourseReview.jsx` - Final review before publishing

**Helper Components**:
- `ActionVerbHelper.jsx` - Bloom's taxonomy action verb suggestions
- `TaxonomySelector.jsx` - Learning objective taxonomy selection
- `LearningOutcomeGenerator.jsx` - AI-assisted outcome generation
- `ConceptEditor.jsx` - Edit concept details

**Backend Endpoints** (`backend/app/routers/courses.py`):
- `POST /courses` - Create new course
- `GET /courses` - List all courses
- `GET /courses/{course_id}` - Get course details
- `PUT /courses/{course_id}` - Update course
- `DELETE /courses/{course_id}` - Delete course
- `POST /courses/{course_id}/modules` - Add module
- `POST /courses/{course_id}/import-cc` - Import Common Cartridge
- `GET /courses/{course_id}/export` - Export course

**Features**:
- AI-powered assessment generation
- Bloom's taxonomy integration
- Quality Matters standards alignment
- PDF content extraction for source materials
- Common Cartridge import/export

### 9. Content Caching (`backend/app/content_cache.py`)

**Purpose**: Reduce AI generation costs by caching generated content

**Schema**: SQLite database with tables for:
- Generated questions
- Generated scenarios
- Content fingerprinting
- Cache expiration

---

## Development Workflows

### Setting Up Local Environment

**Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend Setup**:
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

**Environment Variables** (`.env`):
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ENVIRONMENT=development
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
MASTERY_THRESHOLD=0.85
CONTINUE_THRESHOLD=0.70
MIN_ASSESSMENTS_FOR_MASTERY=3
```

### Git Workflow

**Branch Strategy**:
- `main` - Production-ready code
- `claude/*` - AI assistant working branches (auto-created)
- Feature branches as needed

**Commit Message Format**:
```
Action: Brief description

Detailed explanation of changes:
- Bullet point 1
- Bullet point 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Common Git Commands**:
```bash
git status
git add .
git commit -m "Message"
git push -u origin branch-name
git fetch origin branch-name
git pull origin branch-name
```

### API Testing

**Interactive API Docs**:
- Development: http://localhost:8000/docs
- Production: https://your-app.onrender.com/docs

**Key Endpoints**:
```
GET  /health                         # Health check
POST /start                          # Initialize learner
POST /chat                           # Send message to tutor
GET  /progress/{learner_id}          # Get learner progress
GET  /concepts                       # List all concepts
GET  /concept/{concept_id}           # Get concept metadata
GET  /mastery/{learner_id}/{concept_id}  # Check mastery
POST /courses                        # Create course
GET  /courses/{course_id}            # Get course details
```

### Debugging

**Backend Logs**:
```bash
# Watch logs in development
tail -f backend/logs/*.log

# Check learner model
cat backend/data/learner-models/user_123.json | python -m json.tool
```

**Frontend Console**:
- React DevTools browser extension
- Console.log statements in components
- Network tab for API calls

---

## Testing and Deployment

### Testing

**Backend Tests**:
```bash
cd backend
pytest tests/
pytest tests/test_specific.py -v
```

**Manual Testing**:
- Use `/docs` endpoint for API testing
- Test files: `backend/test_quick.py`, `backend/test_simple.py`
- Frontend test pages: `frontend/test-*.html`

### Deployment (Render.com)

**Configuration**: `render.yaml`
```yaml
services:
  - type: web
    name: adaptive-latin-backend
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT

  - type: web
    name: adaptive-latin-frontend
    buildCommand: cd frontend && npm install && npm run build
    startCommand: cd frontend && npm run preview
```

**Environment Variables on Render**:
- `ANTHROPIC_API_KEY` - Required
- `ENVIRONMENT` - production
- `DEBUG` - False
- `LOG_LEVEL` - INFO
- `CORS_ORIGINS` - Frontend URL

**Deployment Trigger**: Auto-deploy on push to `main` branch

---

## Coding Conventions

### Python (Backend)

**Style**:
- Follow PEP 8
- Use type hints: `def function(param: str) -> Dict[str, Any]`
- Docstrings for all functions:
  ```python
  def load_resource(concept_id: str, resource_type: str) -> Dict[str, Any]:
      """
      Load a resource from the resource bank.

      Args:
          concept_id: Concept identifier (e.g., "concept-001")
          resource_type: Type of resource ("text-explainer" or "examples")

      Returns:
          Resource data as dictionary

      Raises:
          FileNotFoundError: If resource doesn't exist
      """
  ```

**Logging**:
```python
logger.info("Operation completed successfully")
logger.error(f"Error occurred: {e}")
logger.debug("Debug information")
```

**Error Handling**:
```python
try:
    result = operation()
    return result
except SpecificError as e:
    logger.error(f"Specific error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**FastAPI Patterns**:
```python
@app.post("/endpoint")
async def endpoint(request: RequestModel) -> ResponseModel:
    """Endpoint docstring"""
    # Validate input
    # Process request
    # Return response
    return ResponseModel(data=result)
```

### JavaScript/React (Frontend)

**Style**:
- Use functional components with hooks
- Props destructuring: `function Component({ prop1, prop2 })`
- State management: `useState`, `useEffect`
- API calls in `useEffect` or event handlers

**Component Pattern**:
```jsx
function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const handleEvent = () => {
    // Event handler
  };

  return (
    <div className="my-component">
      {/* JSX */}
    </div>
  );
}

export default MyComponent;
```

**API Calls**:
```javascript
// In api.js
export async function apiFunction(param) {
  const response = await fetch(`${API_BASE_URL}/endpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ param })
  });
  return await response.json();
}

// In component
import { apiFunction } from './api';

const result = await apiFunction(param);
```

### File Naming
- Python: `snake_case.py`
- JavaScript/React: `PascalCase.jsx` (components), `camelCase.js` (utilities)
- JSON: `kebab-case.json`
- Markdown: `UPPERCASE.md` (docs), `kebab-case.md` (content)

### Comments
- Use comments to explain **why**, not **what**
- Document complex logic
- Add TODO comments for future improvements: `# TODO: Implement feature X`

---

## Common Tasks

### 1. Adding a New Concept to Latin Grammar Course

**Steps**:
1. Create directory structure:
   ```bash
   mkdir -p resource-bank/latin-grammar/concept-008/{resources,assessments}
   ```

2. Create `metadata.json`:
   ```json
   {
     "id": "concept-008",
     "title": "New Concept",
     "domain": "latin-grammar",
     "difficulty": 3,
     "prerequisites": ["concept-007"],
     "learning_objectives": ["..."],
     "vocabulary": [...]
   }
   ```

3. Create teaching content:
   - `resources/text-explainer.md` (200-500 lines)
   - `resources/examples.json`

4. Create assessments:
   - `assessments/dialogue-prompts.json` (10-15 prompts)
   - `assessments/written-prompts.json` (5-10 prompts)
   - `assessments/applied-tasks.json` (10-15 tasks)

5. Update course metadata if needed

6. Test loading the concept via API

### 2. Modifying AI Agent Behavior

**File**: `backend/prompts/tutor-agent-system-prompt-active.md`

**Steps**:
1. Edit the system prompt file
2. Test changes by starting a new conversation
3. Monitor agent responses in logs
4. Iterate until desired behavior achieved

**Note**: Changes take effect immediately (no restart needed due to file loading)

### 3. Adding a New API Endpoint

**Recommended Approach**: Add to appropriate router in `backend/app/routers/`

**Steps**:
1. Choose the appropriate router file (or create new one):
   - `chat.py` - Conversation-related endpoints
   - `concepts.py` - Concept management
   - `content.py` - Content generation
   - `courses.py` - Course management
   - `learner.py` - Individual learner operations
   - `learners.py` - Learner collection operations
   - `conversations.py` - Conversation history

2. Define Pydantic models in `backend/app/schemas.py`:
   ```python
   class RequestModel(BaseModel):
       field1: str
       field2: int

   class ResponseModel(BaseModel):
       result: str
   ```

3. Create endpoint in the router:
   ```python
   from fastapi import APIRouter, HTTPException
   from ..schemas import RequestModel, ResponseModel

   router = APIRouter()

   @router.post("/new-endpoint", response_model=ResponseModel)
   async def new_endpoint(request: RequestModel):
       """Endpoint description"""
       try:
           # Process request
           return ResponseModel(result="success")
       except Exception as e:
           logger.error(f"Error in new_endpoint: {e}")
           raise HTTPException(status_code=500, detail=str(e))
   ```

4. Register router in `backend/app/main.py` (if creating new router):
   ```python
   from app.routers import new_router
   app.include_router(new_router.router, prefix="/api", tags=["new"])
   ```

5. Test in `/docs`

6. Update frontend API client (`frontend/src/api.js`)

### 4. Adding a New Frontend Component

**Steps**:
1. Create component file: `frontend/src/components/MyComponent.jsx`

2. Implement component:
   ```jsx
   function MyComponent({ prop1 }) {
     return <div>{prop1}</div>;
   }

   export default MyComponent;
   ```

3. Create CSS file: `frontend/src/components/MyComponent.css`

4. Import in parent component:
   ```jsx
   import MyComponent from './components/MyComponent';
   ```

5. Use in JSX: `<MyComponent prop1="value" />`

### 5. Debugging a Learner Model Issue

**Steps**:
1. Find learner model file:
   ```bash
   cat backend/data/learner-models/user_123.json | python -m json.tool
   ```

2. Check recent assessments:
   ```python
   learner_model['concepts']['concept-001']['assessments']
   ```

3. Verify mastery calculation:
   ```bash
   curl http://localhost:8000/mastery/user_123/concept-001
   ```

4. Check logs for errors:
   ```bash
   grep "user_123" backend/logs/*.log
   ```

### 6. Creating a User Course

**Via API**:
```bash
curl -X POST http://localhost:8000/courses \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Course",
    "description": "...",
    "domain": "custom",
    "modules": [...]
  }'
```

**Via Frontend**:
1. Navigate to course creation wizard
2. Fill in course details
3. Plan modules/concepts
4. Create teaching content
5. Add assessments
6. Publish course

### 7. Updating Dependencies

**Backend**:
```bash
cd backend
pip install --upgrade package-name
pip freeze > requirements.txt
```

**Frontend**:
```bash
cd frontend
npm update package-name
npm install
```

### 8. Viewing Content Cache

**Query cache database**:
```bash
sqlite3 backend/content_cache.db
.tables
SELECT * FROM questions LIMIT 10;
.quit
```

### 9. Implementing a Teaching Moment (NEW)

**Purpose**: Provide immediate, interactive feedback for misconceptions

**Steps**:
1. Detect misconception in learner response (in tutor agent or assessment grading)

2. Return Teaching Moment content type from backend:
   ```python
   {
       "content_type": "teaching-moment",
       "misconception": "Using nominative case for direct object",
       "correct_concept": "Direct objects require accusative case",
       "hint": "Look at the ending of 'puellam' - does it show accusative?",
       "example": "Poeta puellam amat (The poet loves the girl)",
       "explanation": "In Latin, case endings show grammatical function..."
   }
   ```

3. Frontend `TeachingMoment.jsx` component will:
   - Display the misconception clearly
   - Show progressive hints
   - Provide worked example
   - Allow learner to try again with guidance

**Best Practices**:
- Use for immediate correction (don't let misconceptions persist)
- Provide scaffolded hints (start general, get specific)
- Include a correct example for reference
- Track whether misconception is resolved

---

## Key Files Reference

### Critical Files (Never Modify Without Understanding)

1. **`backend/app/agent.py`**
   - Core AI agent orchestration
   - Tool definitions for Claude
   - Conversation handling

2. **`backend/app/tools.py`**
   - Resource loading functions
   - Learner model management
   - Mastery calculation logic

3. **`backend/app/main.py`**
   - FastAPI application setup and initialization
   - Middleware configuration (CORS, rate limiting)
   - Router registration

4. **`backend/app/routers/`** (NEW - Modular architecture)
   - `chat.py` - All conversation endpoints (~6.5k lines)
   - `content.py` - Content generation (~22k lines)
   - `courses.py` - Course management (~16k lines)
   - `learner.py` - Learner operations (~8.9k lines)
   - `learners.py` - Learner collection (~11.8k lines)
   - `conversations.py` - Conversation history (~6.7k lines)
   - `concepts.py` - Concept management (~1.8k lines)

5. **`backend/app/pedagogical_tools.py`** (NEW)
   - AI-powered content personalization
   - Contextualized example generation
   - Misconception detection

6. **`frontend/src/App.jsx`** (163 lines)
   - Main application component
   - Route handling
   - State management

### Configuration Files

- **`backend/.env`** - Environment variables (NEVER commit!)
- **`backend/app/config.py`** - Configuration management
- **`render.yaml`** - Deployment configuration
- **`frontend/vite.config.js`** - Vite build configuration

### Documentation Files

- **`ARCHITECTURE.md`** - System architecture (read first!)
- **`COURSE_CREATION_REQUIREMENTS.md`** - Course creation specs
- **`IMPLEMENTATION-ROADMAP.md`** - Development roadmap
- **`CHANGELOG.md`** - Version history (update with changes!)
- **`STATUS.md`** - Current project status

### Content Files

- **`resource-bank/latin-grammar/concept-*/`** - Official Latin course
- **`resource-bank/user-courses/`** - User-generated courses
- **`backend/prompts/`** - AI agent system prompts

---

## Adding New Features

### Planning Process

1. **Review Architecture**: Read `ARCHITECTURE.md` to understand system design
2. **Check Requirements**: See if feature aligns with project goals
3. **Design API**: Define endpoints, request/response models
4. **Plan Components**: Identify backend and frontend changes needed
5. **Consider Testing**: How will you test the feature?

### Implementation Checklist

Backend:
- [ ] Update `backend/app/main.py` with new endpoints
- [ ] Add Pydantic schemas in `backend/app/schemas.py`
- [ ] Implement business logic in appropriate module
- [ ] Add logging statements
- [ ] Handle errors with try-catch
- [ ] Test endpoints in `/docs`
- [ ] Update `backend/README.md` if needed

Frontend:
- [ ] Create new components in `frontend/src/components/`
- [ ] Add API functions in `frontend/src/api.js`
- [ ] Update parent components to integrate
- [ ] Style with CSS (component-scoped)
- [ ] Test in browser
- [ ] Check responsive design

Documentation:
- [ ] Update `CHANGELOG.md` with changes
- [ ] Add comments to complex code
- [ ] Update README if feature is user-facing
- [ ] Document new API endpoints

Deployment:
- [ ] Test locally (backend + frontend together)
- [ ] Commit with descriptive message
- [ ] Push to git (triggers auto-deploy)
- [ ] Monitor Render deployment logs
- [ ] Test in production

### Example: Adding Gamification Feature

**Backend**:
1. Add `points` and `badges` fields to learner model schema
2. Create `calculate_points()` function in `tools.py`
3. Add endpoint `GET /leaderboard` in `main.py`
4. Update `update_learner_model()` to award points

**Frontend**:
1. Create `Leaderboard.jsx` component
2. Add `fetchLeaderboard()` in `api.js`
3. Update `App.jsx` to show leaderboard button
4. Style leaderboard with CSS

**Testing**:
1. Create test learner with various achievements
2. Verify points calculation
3. Check leaderboard displays correctly
4. Test edge cases (no data, ties)

---

## Important Notes for AI Assistants

### When Working on This Codebase

1. **Read Architecture First**: Always review `ARCHITECTURE.md` before making major changes

2. **Understand the Learning Model**: The system is mastery-based, not completion-based. This affects all design decisions.

3. **Preserve Learner Data**: Never modify learner model files directly. Always use tools and API functions.

4. **Test AI Behavior**: Changes to prompts or agent logic should be tested with actual conversations.

5. **Respect the Resource Bank Structure**: Don't modify the JSON/markdown format without updating all related code.

6. **Security Considerations**:
   - Never commit `.env` files
   - Sanitize user input (see `sanitize_user_input()` in main.py)
   - Validate all API inputs with Pydantic
   - Use JWT authentication for protected endpoints

7. **Performance**:
   - Use content caching for AI-generated content
   - Implement pagination for large lists
   - Avoid loading entire course in single request

8. **Backward Compatibility**: Learner models and course formats should be backward-compatible. Add new fields as optional.

9. **Error Messages**: Always provide helpful error messages to users. Log detailed errors for debugging.

10. **Documentation**: Update `CHANGELOG.md` with all changes. Follow semantic versioning.

### Common Pitfalls to Avoid

1. **Don't hardcode paths**: Use `config.get_concept_dir()` instead of string paths
2. **Don't assume concept IDs**: Always validate concept exists before loading
3. **Don't skip validation**: Use Pydantic models for all API inputs
4. **Don't ignore confidence scores**: Mastery is based on multiple assessments, not single score
5. **Don't break the conversation flow**: Maintain conversation history properly
6. **Don't modify course structure without migration**: Existing courses must still load
7. **Don't forget CORS**: Frontend and backend are separate origins
8. **Don't skip error handling**: Wrap API calls in try-catch blocks

### Best Practices

1. **Incremental Changes**: Make small, testable changes rather than large refactors
2. **Test Locally First**: Always test backend and frontend integration before deploying
3. **Use Type Hints**: Python type hints help catch errors early
4. **Log Important Events**: Use logging for debugging and monitoring
5. **Follow Existing Patterns**: Match the style of existing code
6. **Document Complex Logic**: Add comments explaining "why", not "what"
7. **Version Control**: Commit frequently with clear messages
8. **Monitor Production**: Check Render logs after deployment

---

## Support and Resources

### Documentation
- **Primary**: This file (`CLAUDE.md`)
- **Architecture**: `ARCHITECTURE.md`
- **Backend**: `backend/README.md`
- **Course Creation**: `COURSE_CREATION_REQUIREMENTS.md`

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Anthropic API**: https://docs.anthropic.com/
- **Render Deployment**: https://render.com/docs

### Getting Help
- Review existing code for patterns
- Check logs for error messages
- Test endpoints in `/docs`
- Review Git history for similar changes

---

## Version History

**v1.1.0** (2025-11-19) - Major architecture and feature updates
- Updated to reflect modular router-based backend architecture
- Added documentation for pedagogical_tools.py and constants.py
- Documented Teaching Moment assessment type
- Added comprehensive frontend component list (50+ components)
- Corrected line counts (previous estimates were inflated)
- Added new course creation components:
  - OnboardingQuestionBuilder
  - AssessmentBuilder with AI generation
  - Enhanced taxonomy integration
- Updated dependency versions (anthropic >= 0.71.0, react-router-dom 7.9.6)
- Added admin components, learner components, and interactive widgets
- Expanded router endpoint documentation
- Added information about canvas-confetti for celebration effects

**v1.0.0** (2025-11-17) - Initial CLAUDE.md creation
- Comprehensive codebase documentation
- Development workflow guidance
- Common tasks and examples
- AI assistant best practices

---

**End of CLAUDE.md**

This document should be updated whenever major architectural changes occur or new patterns are established.
