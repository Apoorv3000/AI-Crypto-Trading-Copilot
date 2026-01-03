"""LangGraph workflow definition.

⚠️  DEPRECATED: This file is kept for backward compatibility only.
    Use hierarchical_graph.py for all new code.

Defines the multi-agent decision workflow using LangGraph.
"""

# This file is deprecated - imports commented out to prevent errors
# Use hierarchical_graph.py instead

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from ..context.schema import DecisionContext
# from ..agents import (
#     market_agent,
#     ml_agent,
#     sentiment_agent,
#     risk_agent,
#     decision_agent,
#     evaluator_agent,
# )
# from .router import route_next_agent
from ..utils.logger import get_logger

logger = get_logger(__name__)


def create_decision_graph() -> StateGraph:
    """Create the LangGraph workflow for trading decisions.
    
    ⚠️  DEPRECATED: Use create_hierarchical_graph() from hierarchical_graph.py instead.
    
    This function is kept for backward compatibility but is non-functional.
    """
    logger.warning("create_decision_graph() is DEPRECATED. Use create_hierarchical_graph() instead.")
    raise NotImplementedError(
        "create_decision_graph() is deprecated. "
        "Use create_hierarchical_graph() from hierarchical_graph.py instead."
    )


def create_simple_decision_graph() -> StateGraph:
    """Create a simplified 2-agent workflow (for initial testing).
    
    ⚠️  DEPRECATED: Use create_hierarchical_graph() from hierarchical_graph.py instead.
    
    This function is kept for backward compatibility but is non-functional.
    """
    logger.warning("create_simple_decision_graph() is DEPRECATED. Use create_hierarchical_graph() instead.")
    raise NotImplementedError(
        "create_simple_decision_graph() is deprecated. "
        "Use create_hierarchical_graph() from hierarchical_graph.py instead."
    )
