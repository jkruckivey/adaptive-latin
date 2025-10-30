"""
FastAPI Application for Latin Adaptive Learning System
"""

import os
import logging
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

from .config import config
from .routers import learners, concepts, conversations
from .database import init_db
from .auth import create_access_token
from fastapi.security import OAuth2PasswordRequestForm

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Request size limit middleware
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 1024 * 1024):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(status_code=413, content={"detail": f"Request body too large. Maximum size is {self.max_size} bytes."})
        return await call_next(request)

# Initialize FastAPI app
app = FastAPI(title="Latin Adaptive Learning API", description="Backend API for AI-powered adaptive Latin grammar learning", version="1.0.0")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})

# Add middleware
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "OPTIONS"], allow_headers=["Content-Type", "Authorization", "Accept"])

# Include routers
app.include_router(learners.router, prefix="/learners", tags=["Learners"])
app.include_router(concepts.router, prefix="/concepts", tags=["Concepts"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real app, you'd verify the username and password against a database.
    # For this example, we'll just use a dummy user.
    if form_data.username == "jules" and form_data.password == "verne":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Latin Adaptive Learning API...")
    config.validate()
    config.ensure_directories()
    init_db()
    # ... (rest of startup logic from original main.py)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Latin Adaptive Learning API...")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG, log_level=config.LOG_LEVEL.lower())
