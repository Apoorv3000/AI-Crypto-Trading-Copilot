"""FastAPI service for the AI Decision Engine.

Provides HTTP endpoints for making trading decisions.
"""

from .server import app
from .routes import router
from .models import DecisionRequest, DecisionResponse

__all__ = [
    "app",
    "router",
    "DecisionRequest",
    "DecisionResponse",
]
