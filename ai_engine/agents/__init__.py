"""Subgraphs package - each subgraph is a self-contained worker + evaluator."""

from .market.graph import create_market_subgraph
from .sentiment.graph import create_sentiment_subgraph
from .risk.graph import create_risk_subgraph
from .ml.graph import create_ml_subgraph

__all__ = [
    "create_market_subgraph",
    "create_sentiment_subgraph",
    "create_risk_subgraph",
    "create_ml_subgraph",
]
