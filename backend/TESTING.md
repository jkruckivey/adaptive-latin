# Local Testing Guide

## Prerequisites

✅ Virtual environment created
✅ Dependencies installed
✅ Data directories created
⚠️ **REQUIRED:** Add your Anthropic API key to `.env` file

## Step 1: Add API Key

Edit `backend/.env` and replace:
```
ANTHROPIC_API_KEY=your_api_key_here
```

With your actual key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Get your API key from: https://console.anthropic.com/

## Step 2: Start the Server

### Windows (Git Bash)
```bash
cd "C:\Users\jkruck\Ivey Business School\EdTech Lab - Documents\Github\Actually Self Paced Course\backend"
source venv/Scripts/activate
uvicorn app.main:app --reload
```

### Alternative (PowerShell)
```powershell
cd "C:\Users\jkruck\Ivey Business School\EdTech Lab - Documents\Github\Actually Self Paced Course\backend"
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Test the API

### Option A: Interactive API Documentation
Visit http://localhost:8000/docs in your browser

This provides a Swagger UI where you can test all endpoints interactively.

### Option B: Command Line Tests

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

#### 2. Start a New Learner
```bash
curl -X POST "http://localhost:8000/start" \
  -H "Content-Type: application/json" \
  -d '{"learner_id": "test-learner-001", "name": "Test Student"}'
```

Expected response:
```json
{
  "learner_id": "test-learner-001",
  "current_concept": "concept-001",
  "message": "Welcome! Let's begin your Latin journey..."
}
```

#### 3. Send a Chat Message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"learner_id": "test-learner-001", "message": "What is first declension?"}'
```

Expected response:
```json
{
  "response": "[AI tutor response explaining first declension]",
  "confidence": null,
  "current_concept": "concept-001"
}
```

#### 4. Get Progress
```bash
curl http://localhost:8000/progress/test-learner-001
```

Expected response:
```json
{
  "learner_id": "test-learner-001",
  "current_concept": "concept-001",
  "completed_concepts": [],
  "concept_mastery": {...}
}
```

#### 5. Get Available Concepts
```bash
curl http://localhost:8000/concepts
```

Expected response:
```json
{
  "concepts": [
    {
      "id": "concept-001",
      "title": "First Declension Nouns + Sum, esse (present)",
      "difficulty": 1,
      "prerequisites": []
    },
    ...
  ]
}
```

## Step 4: Test a Complete Learning Session

Try this interactive conversation flow:

1. **Start**: Create a learner
2. **Introduction**: Ask "What will I learn today?"
3. **Resource Request**: The AI should load text-explainer or examples
4. **Assessment**: The AI will ask questions from dialogue-prompts.json
5. **Confidence Rating**: After you answer, rate your confidence (1-5)
6. **Feedback**: AI provides calibration-aware feedback
7. **Progress Check**: Use `/progress` endpoint to see updated scores

## Common Issues

### "Connection refused"
- Make sure the server is running
- Check that you're on the right port (8000)

### "API key not found"
- Verify `.env` file has your actual API key
- Restart the server after adding the key

### "Resource not found"
- Verify `resource-bank/latin-grammar/concept-001/` exists
- Check `examples/prompts/` directory exists

### "Module import error"
- Make sure you're in the virtual environment (`source venv/Scripts/activate`)
- Re-run `pip install -r requirements.txt`

## Monitoring Logs

The server will log:
- ✅ Resource loads (when AI requests text-explainer or examples)
- ✅ Tool calls (when AI uses track_confidence, update_progress, etc.)
- ✅ Learner model updates
- ✅ API requests and responses

Watch the terminal for these logs to understand what's happening.

## Next Steps After Testing

Once local testing works:
1. Test with multiple learners
2. Test regression scenarios
3. Validate confidence tracking over multiple assessments
4. Deploy to Render (see DEPLOYMENT.md)

## Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check server status |
| `/start` | POST | Create new learner |
| `/chat` | POST | Send message to AI tutor |
| `/progress/{learner_id}` | GET | Get learner progress |
| `/concepts` | GET | List all concepts |
| `/concepts/{concept_id}` | GET | Get concept details |
| `/mastery/{learner_id}/{concept_id}` | GET | Get mastery score |
| `/docs` | GET | Interactive API documentation |
