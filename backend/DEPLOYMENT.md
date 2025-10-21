# Deployment Guide - Render.com

This guide walks through deploying the Latin Adaptive Learning System backend to Render.com.

## Prerequisites

1. GitHub repository with this code
2. Render.com account (free tier available)
3. Anthropic API key

## Step-by-Step Deployment

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Complete FastAPI backend for Latin adaptive learning"
git push origin main
```

### 2. Create Render Web Service

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository

### 3. Configure Build Settings

**Name:** `latin-learning-backend` (or your choice)

**Region:** Choose closest to your users

**Branch:** `main`

**Root Directory:** `backend`

**Runtime:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:** `Free` (or higher for production)

### 4. Add Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Your actual API key |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Model version |
| `ENVIRONMENT` | `production` | Production environment |
| `DEBUG` | `False` | Disable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `https://yourfrontend.com` | Your frontend URL |
| `MASTERY_THRESHOLD` | `0.85` | Mastery threshold |
| `CONTINUE_THRESHOLD` | `0.70` | Continue threshold |
| `MIN_ASSESSMENTS_FOR_MASTERY` | `3` | Min assessments |

**Important:** Update `CORS_ORIGINS` to match your actual frontend URL. For multiple origins, separate with commas:
```
https://yourfrontend.com,https://app.yourdomain.com
```

### 5. Configure Health Check (Optional)

**Health Check Path:** `/health`

This allows Render to monitor your service health.

### 6. Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start the server
   - Assign a URL (e.g., `https://latin-learning-backend.onrender.com`)

### 7. Monitor Deployment

Watch the deployment logs in real-time. You should see:

```
Starting Latin Adaptive Learning API...
Configuration validated successfully
Environment: production
Resource bank: /opt/render/project/src/resource-bank/latin-grammar
Learner models: /opt/render/project/src/backend/data/learner-models
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

### 8. Test Deployment

Once deployed, test the health endpoint:

```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

## Post-Deployment

### Update Frontend

Update your frontend to use the Render URL:

```javascript
const API_URL = 'https://your-app.onrender.com';
```

### Test API Endpoints

Visit the interactive API docs:
```
https://your-app.onrender.com/docs
```

Test the `/start` endpoint to create a new learner:
```bash
curl -X POST https://your-app.onrender.com/start \
  -H "Content-Type: application/json" \
  -d '{"learner_id": "test_user"}'
```

### Monitor Logs

View logs in Render dashboard:
1. Go to your service
2. Click **"Logs"** tab
3. Watch real-time logs

### Check Metrics

Render provides metrics:
- CPU usage
- Memory usage
- Request count
- Response times

## Troubleshooting

### Build Fails

**Error:** `No module named 'app'`

**Solution:** Make sure Root Directory is set to `backend`

---

**Error:** `requirements.txt not found`

**Solution:** Verify the file exists in the `backend/` directory

### Service Won't Start

**Error:** `Configuration errors: ANTHROPIC_API_KEY is required`

**Solution:** Add `ANTHROPIC_API_KEY` in environment variables

---

**Error:** `Resource bank directory not found`

**Solution:** Ensure the resource bank is in the repository at the correct path

### CORS Errors

**Error:** Frontend gets CORS errors

**Solution:** Update `CORS_ORIGINS` environment variable to include your frontend URL

### Port Issues

**Error:** `Address already in use`

**Solution:** Render automatically sets `$PORT`. Don't hardcode port 8000 in start command.

Use: `--port $PORT` (not `--port 8000`)

## Free Tier Limitations

Render's free tier:
- ✅ 750 hours/month
- ✅ Automatic SSL
- ✅ Auto-deploy from GitHub
- ⚠️ Spins down after 15 min of inactivity (first request may be slow)
- ⚠️ Limited CPU/memory

For production, consider upgrading to paid tier ($7/month) for:
- No spin down
- More resources
- Better performance

## Upgrading

To upgrade your plan:
1. Go to your service settings
2. Click **"Upgrade"**
3. Select a paid plan

## Auto-Deploy

Render automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Update backend"
git push origin main
# Render automatically deploys
```

To disable auto-deploy:
1. Go to service settings
2. Disable **"Auto-Deploy"**

## Environment-Specific Configs

Create different services for staging/production:

**Staging:**
- Branch: `develop`
- Environment: `staging`
- CORS: `https://staging.yourapp.com`

**Production:**
- Branch: `main`
- Environment: `production`
- CORS: `https://yourapp.com`

## Database Migration (Future)

When moving from JSON files to PostgreSQL:

1. Add Render PostgreSQL database
2. Update environment variable: `DATABASE_URL`
3. Modify `tools.py` to use database instead of JSON files
4. Deploy changes

## Security Best Practices

1. **Never commit `.env` file** (use environment variables)
2. **Rotate API keys regularly**
3. **Use HTTPS only** (Render provides free SSL)
4. **Validate all inputs** (Pydantic models handle this)
5. **Monitor logs** for suspicious activity
6. **Set rate limits** (add middleware if needed)

## Support

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com/
- **Support:** https://render.com/support

## Cost Estimate

**Free Tier:**
- Backend: $0/month
- Total: $0/month

**Starter Plan:**
- Backend: $7/month
- PostgreSQL (if added): $7/month
- Total: $7-14/month

**Professional:**
- Backend: $25/month
- PostgreSQL: $20/month
- Total: $45/month

## Next Steps

1. Deploy backend to Render
2. Build frontend (React/Vite)
3. Deploy frontend to Vercel/Netlify
4. Connect frontend to backend API
5. Test complete user flow
6. Monitor usage and performance
7. Scale as needed
