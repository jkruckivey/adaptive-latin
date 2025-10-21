"""
Latin Adaptive Learning System - Backend Package

A production-ready FastAPI backend for an AI-powered adaptive learning system
that teaches Latin grammar using Claude AI with confidence tracking and
personalized sequencing.
"""

__version__ = "1.0.0"
__author__ = "James Kruck"
__description__ = "Adaptive learning backend with Claude AI integration"

from .config import config
from .main import app

__all__ = ["app", "config"]
