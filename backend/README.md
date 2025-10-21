# Latin Adaptive Learning System - Backend API

A production-ready FastAPI backend for an AI-powered adaptive learning system that teaches Latin grammar using Claude AI with confidence tracking and personalized sequencing.

## Features

- **Adaptive Learning**: Continuous assessment with personalized sequencing based on mastery
- **Claude AI Integration**: Natural language tutoring with tool use for resource loading and progress tracking
- **Confidence Tracking**: Metacognitive awareness through self-assessment calibration
- **Multi-Modal Assessment**: Dialogue, written, and applied task assessments
- **RESTful API**: Clean REST endpoints with Pydantic validation
- **Production Ready**: Configured for Render deployment with health checks and logging

## Architecture

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management (env vars, paths)
│   ├── main.py              # FastAPI application and endpoints
│   ├── agent.py             # Claude API integration with tool use
│   ├── tools.py             # Resource loading and learner model management
│   └── confidence.py        # Confidence tracking and calibration
├── data/
│   └── learner-models/      # JSON files for learner progress (created automatically)
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Prerequisites

- Python 3.11+
- Anthropic API key (get one at https://console.anthropic.com/)
- Access to the resource bank directory (`../resource-bank/latin-grammar/`)

## Quick Start (Local Development)

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 5. Run the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py entry point
python -m app.main
```

### 6. Test the API

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

## Deployment to Render

### 1. Create New Web Service

1. Go to https://render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure build settings:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2. Environment Variables

Add these in Render dashboard:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourfrontend.com
```

### 3. Deploy

Render will automatically deploy when you push to your repository.

Health check endpoint: `https://your-app.onrender.com/health`

## API Endpoints

### Health Check

```
GET /health
```

Returns application status and version.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### Start New Learner

```
POST /start
```

Initialize a new learner session.

**Request:**
```json
{
  "learner_id": "user_123"
}
```

**Response:**
```json
{
  "success": true,
  "learner_id": "user_123",
  "current_concept": "concept-001",
  "message": "Learner initialized successfully. Ready to begin learning!"
}
```

### Chat with Tutor

```
POST /chat
```

Send a message to the AI tutor and get a response.

**Request:**
```json
{
  "learner_id": "user_123",
  "message": "I'm ready to start learning Latin!",
  "conversation_history": []
}
```

**Response:**
```json
{
  "success": true,
  "message": "Welcome! Let's begin with first declension nouns...",
  "conversation_history": [...]
}
```

### Get Progress

```
GET /progress/{learner_id}
```

Get detailed progress information for a learner.

**Response:**
```json
{
  "learner_id": "user_123",
  "current_concept": "concept-002",
  "concepts_completed": 1,
  "concepts_in_progress": 1,
  "total_assessments": 8,
  "average_calibration_accuracy": 0.85,
  "concept_details": {...},
  "overall_calibration": {...}
}
```

### Get Concept Info

```
GET /concept/{concept_id}
```

Get metadata about a specific concept.

**Response:**
```json
{
  "concept_id": "concept-001",
  "title": "First Declension Nouns + Sum, esse (present)",
  "difficulty": 1,
  "prerequisites": [],
  "learning_objectives": [...],
  "estimated_mastery_time": "60-90 minutes",
  "vocabulary": [...]
}
```

### Get Mastery Status

```
GET /mastery/{learner_id}/{concept_id}
```

Calculate mastery level for a concept.

**Response:**
```json
{
  "concept_id": "concept-001",
  "mastery_achieved": true,
  "mastery_score": 0.88,
  "assessments_completed": 5,
  "recommendation": "progress",
  "reason": "Mastery achieved: 0.88 average across 5 assessments"
}
```

### List All Concepts

```
GET /concepts
```

Get a list of all available concepts.

**Response:**
```json
{
  "success": true,
  "concepts": ["concept-001", "concept-002", ...],
  "total": 7
}
```

## How It Works

### 1. Learner Model Persistence

Each learner's progress is stored in a JSON file at `data/learner-models/{learner_id}.json`:

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
  "overall_progress": {...}
}
```

### 2. Claude AI Tool Use

The agent can use these tools during conversation:

- `load_resource` - Fetch text explanations or examples
- `load_assessment` - Get dialogue prompts, written prompts, or applied tasks
- `load_concept_metadata` - Get concept information
- `track_confidence` - Calculate calibration between confidence and performance
- `update_learner_model` - Record assessment results
- `calculate_mastery` - Check if mastery criteria met
- `get_next_concept` - Determine next concept in sequence

### 3. Confidence Tracking

After each assessment:
1. Learner rates confidence (1-5)
2. Agent scores performance (0.0-1.0)
3. System calculates calibration error
4. Agent provides calibration-aware feedback

### 4. Mastery-Based Progression

Agent decides next action based on:
- **Progress** (≥0.85 average, 3+ assessments): Move to next concept
- **Continue** (0.70-0.84): More practice on current concept
- **Support** (<0.70): Different approach or review prerequisites

## Configuration

All configuration is managed through environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required) | - |
| `ANTHROPIC_MODEL` | Claude model to use | `claude-3-5-sonnet-20241022` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `MASTERY_THRESHOLD` | Score required for mastery | `0.85` |
| `CONTINUE_THRESHOLD` | Score for continued practice | `0.70` |
| `MIN_ASSESSMENTS_FOR_MASTERY` | Minimum assessments needed | `3` |

## Logging

Application uses Python's built-in logging. Logs include:

- API requests and responses
- Tool executions
- Learner model updates
- Errors and exceptions

In production, logs are visible in Render dashboard.

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created (new learner)
- `400 Bad Request` - Invalid input
- `404 Not Found` - Learner or concept not found
- `409 Conflict` - Learner already exists
- `500 Internal Server Error` - Server error

Error responses include detailed messages:

```json
{
  "detail": "Learner not found: user_123"
}
```

## Development

### Run Tests (Future)

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

### Update Dependencies

```bash
pip freeze > requirements.txt
```

## Troubleshooting

### "ANTHROPIC_API_KEY is required"

Make sure you've created a `.env` file with your API key:
```bash
cp .env.example .env
# Edit .env and add your key
```

### "Resource bank directory not found"

Ensure the resource bank exists at the correct path:
```
../resource-bank/latin-grammar/concept-001/
../resource-bank/latin-grammar/concept-002/
...
```

### CORS Errors

Update `CORS_ORIGINS` in `.env` to include your frontend URL.

### Port Already in Use

Change the port in `.env` or when running:
```bash
uvicorn app.main:app --port 8001
```

## License

MIT License

## Support

For issues or questions, contact the development team.
