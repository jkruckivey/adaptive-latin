import os
import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from . import config
from .schemas import HealthResponse
from .routers import learner, chat, content, courses

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Latin Adaptive Learning API",
    description="Backend for the Adaptive Latin Learning System",
    version="0.1.0"
)

# Set up rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject limiter into routers
chat.limiter = limiter
content.limiter = limiter

# Include routers
app.include_router(learner.router, tags=["Learner"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(content.router, tags=["Content"])
app.include_router(courses.router, tags=["Courses"])

@app.on_event("startup")
async def startup_event():
    """Validate configuration and ensure directories exist on startup."""
    try:
        logger.info("Starting Latin Adaptive Learning API...")
        config.validate()
        config.ensure_directories()

        # Initialize content cache database
        try:
            from .content_cache import init_database
            init_database()
            logger.info("✅ Content cache database initialized")
        except Exception as e:
            logger.warning(f"⚠️  Content cache initialization failed: {e}")
            logger.warning("⚠️  Content caching will not be available")

        # Log directory status for debugging
        logger.info(f"Learner models directory: {config.LEARNER_MODELS_DIR}")
        logger.info(f"Directory exists: {config.LEARNER_MODELS_DIR.exists()}")
        logger.info(f"Directory writable: {os.access(config.LEARNER_MODELS_DIR, os.W_OK)}")

        # Test write permissions
        test_file = config.LEARNER_MODELS_DIR / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            logger.info("✅ Learner models directory is writable")
        except Exception as e:
            logger.error(f"❌ Cannot write to learner models directory: {e}")
            logger.warning("⚠️  Learner data will not persist! Consider using a database or persistent storage.")

        # Validate CORS configuration for production safety
        if "*" in config.CORS_ORIGINS:
            if config.ENVIRONMENT == "production":
                raise ValueError("CORS wildcard (*) is not allowed in production. Please specify explicit origins.")
            else:
                logger.warning("⚠️  CORS wildcard (*) detected - acceptable for development but NOT for production!")

        # Production storage warning
        if config.ENVIRONMENT == "production":
            logger.warning("⚠️  PRODUCTION MODE: Using local filesystem for learner data.")
            logger.warning("⚠️  Data will be lost on container restart. Consider using a database for persistence.")

        logger.info("Configuration validated successfully")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"CORS Origins: {', '.join(config.CORS_ORIGINS)}")
        logger.info(f"Resource bank: {config.RESOURCE_BANK_DIR}")
        logger.info(f"Learner models: {config.LEARNER_MODELS_DIR}")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        raise

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint redirecting to docs."""
    return {"message": "Latin Adaptive Learning API is running. Visit /docs for API documentation."}

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": config.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
