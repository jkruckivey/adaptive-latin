# Quick Start Guide

## ✅ What's Already Set Up

- ✅ Python virtual environment created (`venv/`)
- ✅ All dependencies installed (FastAPI, Anthropic, etc.)
- ✅ Data directories created (`data/learner-models/`)
- ✅ Configuration file created (`.env`)
- ✅ 7 Latin grammar concepts authored (concept-001 through concept-007)
- ✅ System prompts and confidence tracking ready
- ✅ FastAPI application with 7 REST endpoints

## ⚠️ What You Need to Do

### 1. Add Your Anthropic API Key

Edit `backend/.env` file and replace:
```
ANTHROPIC_API_KEY=your_api_key_here
```

With your actual key from https://console.anthropic.com/

### 2. Start the Server

**Option A: Use the start script (Git Bash)**
```bash
./start-server.sh
```

**Option B: Use the batch file (Windows Command Prompt)**
```cmd
start-server.bat
```

**Option C: Manual start (any terminal)**
```bash
source venv/Scripts/activate  # Windows Git Bash
# OR
.\venv\Scripts\Activate.ps1   # PowerShell
# OR
venv\Scripts\activate.bat     # Windows CMD

# Then start the server
uvicorn app.main:app --reload
```

### 3. Verify It's Working

Open http://localhost:8000/docs in your browser

You should see the interactive API documentation.

## 🧪 Quick Test

Try this in a new terminal window:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","environment":"development"}
```

## 📖 Full Testing Guide

See `TESTING.md` for comprehensive testing instructions including:
- How to create a learner
- How to send chat messages
- How to check progress
- Example conversation flows
- Common troubleshooting

## 📂 Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Environment configuration
│   ├── tools.py             # Resource loading & learner management
│   ├── confidence.py        # Confidence tracking & calibration
│   ├── agent.py             # Claude API integration
│   └── main.py              # FastAPI application
├── data/
│   └── learner-models/      # JSON files storing learner progress
├── venv/                     # Python virtual environment
├── .env                      # Environment variables (ADD YOUR API KEY HERE)
├── .env.example              # Template for .env
├── requirements.txt          # Python dependencies
├── README.md                 # Detailed documentation
├── DEPLOYMENT.md             # Render deployment guide
├── TESTING.md                # Testing guide
├── QUICKSTART.md             # This file
├── start-server.sh           # Launch script (Git Bash)
└── start-server.bat          # Launch script (Windows)
```

## 🎯 What This Does

This backend powers an **adaptive AI-driven self-paced Latin course**:

1. **Multi-modal Assessment**: Dialogue, written responses, applied tasks
2. **Confidence Tracking**: Students rate their confidence, AI provides calibration feedback
3. **Adaptive Progression**: Progress when ready, regress when needed
4. **Continuous Assessment**: Entire course is an assessment
5. **Claude AI Tutor**: Uses claude-3-5-sonnet-20241022 with tool use

## 🚀 After Local Testing

Once you've tested locally and everything works:

1. See `DEPLOYMENT.md` for Render deployment instructions
2. Build frontend to connect to this API
3. Pilot with 1-2 actual Latin learners

## 📞 Need Help?

Check these files:
- `README.md` - Comprehensive backend documentation
- `TESTING.md` - Testing instructions and troubleshooting
- `DEPLOYMENT.md` - Deployment guide
- `../ARCHITECTURE.md` - System design overview
- `../IMPLEMENTATION-ROADMAP.md` - Full implementation plan

## 🎓 What's Ready to Test

**7 Complete Latin Concepts:**
1. Concept 001: First Declension + Sum, esse
2. Concept 002: First Conjugation Verbs
3. Concept 003: Second Declension M/N
4. Concept 004: Adjectives + Agreement
5. Concept 005: Perfect System
6. Concept 006: Third Declension
7. Concept 007: Infinitives + Indirect Statement

**Each Concept Includes:**
- Metadata (learning objectives, vocabulary, prerequisites)
- Text explanations (1500-2000 words)
- Examples (5-7 examples)
- Dialogue prompts (6+ questions with rubrics)
- Written prompts (2-3 tasks)
- Applied tasks (3+ exercises)
- Confidence tracking integration

**Total Content:** ~40,000+ lines of authored learning resources!

---

**Ready to go! Just add your API key and start the server. 🎉**
