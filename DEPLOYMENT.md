# Deployment Guide

## System Architecture

Your adaptive Latin learning system consists of two services:

- **Backend API**: https://adaptive-latin-backend.onrender.com
- **Frontend App**: To be deployed at https://adaptive-latin-frontend.onrender.com

## Deployment Steps

### 1. Update Backend CORS Settings (Do this first!)

Go to your Render dashboard for `adaptive-latin-backend` and add this environment variable:

**Key:** `CORS_ORIGINS`
**Value:** `https://adaptive-latin-frontend.onrender.com`

(After you deploy the frontend, if Render gives it a different URL, update this value)

### 2. Deploy the Frontend on Render

#### Option A: Use the render.yaml (Recommended)

1. Go to your Render Dashboard
2. Click "New +" → "Blueprint"
3. Connect your GitHub repo `jkruckivey/adaptive-latin`
4. Render will detect the `render.yaml` and create both services
5. Since your backend already exists, you can skip it and just create the frontend

#### Option B: Manual Static Site Creation

1. Go to Render Dashboard
2. Click "New +" → "Static Site"
3. Connect to your GitHub repo
4. Configure:
   - **Name:** `adaptive-latin-frontend`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
5. Click "Create Static Site"

### 3. Test Your Deployment

Once deployed, your frontend will be at:
`https://adaptive-latin-frontend.onrender.com`

Visit that URL and you should see your onboarding flow!

### 4. If You Need to Update CORS Again

After deploying, if the frontend URL is different, update the backend's `CORS_ORIGINS` environment variable to include it.

## What's Deployed

### Backend Features
- Diagnostic-first learning with confidence calibration
- AI-generated personalized content (Claude Sonnet 4)
- External resources system (24 curated Latin resources)
- Question history tracking (last 10 questions)
- Learner model persistence on disk

### Frontend Features
- Interactive onboarding flow
- Learning preference assessment (visual/connections/practice)
- Confidence calibration interface (4-point scale)
- External resource cards (videos, articles, practice exercises)
- Progress tracking and mastery visualization

### External Resources
- **Videos**: YouTube tutorials for visual learners
- **Articles**: Written guides for conceptual learners
- **Practice**: Interactive exercises for kinesthetic learners
- **Smart filtering**: Resources matched to learner preferences
- **Auto-attachment**: Top 2 resources added to remedial content

## File Structure

```
adaptive-latin/
├── backend/
│   ├── app/
│   │   ├── agent.py          # AI content generation
│   │   ├── config.py         # Configuration settings
│   │   ├── main.py           # FastAPI endpoints
│   │   └── tools.py          # Resource loading, learner models
│   ├── data/
│   │   └── learner-models/   # Persistent learner data (on disk)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── OnboardingFlow.jsx
│   │   │   ├── ExternalResources.jsx
│   │   │   ├── ContentRenderer.jsx
│   │   │   └── content-types/
│   │   ├── api.js            # API client with production URL
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── resource-bank/
│   ├── external-resources.json  # Curated learning resources
│   └── latin-grammar/           # Concept materials
└── render.yaml                  # Deployment configuration
```

## Recent Changes (Commit 90f4447)

- Added external resources system with 24 curated resources
- Fixed file path issue (now looks in resource-bank/ instead of latin-grammar/)
- Added question context and user answer to remediation prompts
- Updated terminology from "learning styles" to "learning preferences"
- Created ExternalResources React component with card-based UI
- Integrated resources into LessonView and ExampleSet components

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console, verify:
1. Backend `CORS_ORIGINS` environment variable includes frontend URL
2. Frontend URL matches exactly (with https://)
3. Backend service has been redeployed after updating env vars

### Resources Not Loading
If external resources don't appear:
1. Check backend logs for "External resources file not found" warning
2. Verify `resource-bank/external-resources.json` exists in deployed code
3. Confirm backend code has latest commit (90f4447 or later)

### Build Failures
If frontend build fails on Render:
1. Check that Node.js version is compatible (16+ recommended)
2. Verify `frontend/package.json` has all dependencies
3. Check build logs for specific npm errors

## Support

For issues, check:
- Backend logs in Render dashboard
- Frontend build logs in Render dashboard
- Browser console for client-side errors
- GitHub repository: https://github.com/jkruckivey/adaptive-latin
