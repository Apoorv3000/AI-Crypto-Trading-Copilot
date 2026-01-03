"""AI Decision Engine for Trading Copilot.

A multi-agent AI system that combines market indicators, ML predictions,
sentiment analysis, and risk management to make intelligent trading decisions.
"""

__version__ = "0.1.0"

from .graph.engine import DecisionEngine
from .context.schema import DecisionContext
from .api.server import app

__all__ = [
    "DecisionEngine",
    "DecisionContext",
    "app",
]
