# GitHub Repository Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new

2. Fill in the details:
   - **Repository name**: `adaptive-latin-learning` (or your preferred name)
   - **Description**: `AI-driven adaptive self-paced Latin grammar course with multi-modal assessment and confidence tracking`
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. Click **Create repository**

## Step 2: Push Your Local Code

After creating the repository, GitHub will show you commands. Use these:

```bash
cd "C:\Users\jkruck\Ivey Business School\EdTech Lab - Documents\Github\Actually Self Paced Course"

# Add the remote (replace USERNAME and REPO_NAME with your values)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Or if you prefer SSH:
# git remote add origin git@github.com:USERNAME/REPO_NAME.git

# Push your code
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

Visit your GitHub repository URL to confirm all files were uploaded.

You should see:
- 77 files
- README.md displayed on the homepage
- All 7 Latin concepts in resource-bank/
- Backend code in backend/

## Important Notes

⚠️ **Security Check**:
- Verify that `.env` file is NOT in your GitHub repository
- Your Anthropic API key should remain private
- Only `.env.example` should be visible

✅ **What Should Be There**:
- All Python source code (backend/app/)
- All Latin learning resources (resource-bank/)
- Documentation files (README.md, ARCHITECTURE.md, etc.)
- Example files (examples/)

❌ **What Should NOT Be There**:
- `.env` file (contains your API key)
- `venv/` directory (Python virtual environment)
- `backend/data/learner-models/*.json` (learner data files)

## Next Step: Deploy to Render

Once your code is on GitHub, you can proceed with Render deployment.

See `backend/DEPLOYMENT.md` for deployment instructions.
