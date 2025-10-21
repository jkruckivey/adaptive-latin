@echo off
REM Start the Latin Adaptive Learning Backend Server (Windows)

echo ============================================
echo  Latin Adaptive Learning Backend Server
echo ============================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found
    echo Please copy .env.example to .env and add your Anthropic API key
    pause
    exit /b 1
)

REM Check if API key is set
findstr /C:"your_api_key_here" .env >nul
if %errorlevel% equ 0 (
    echo WARNING: Please add your Anthropic API key to .env file
    echo    Edit line 4: ANTHROPIC_API_KEY=your_api_key_here
    echo.
    pause
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Start the server
echo.
echo Starting Uvicorn server on http://localhost:8000
echo.
echo  API Documentation: http://localhost:8000/docs
echo  Health Check: http://localhost:8000/health
echo.
echo Press CTRL+C to stop the server
echo ============================================
echo.

uvicorn app.main:app --reload
