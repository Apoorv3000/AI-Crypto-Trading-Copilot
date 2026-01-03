"""Tests for the LangGraph workflow."""

import pytest
from ai_engine.graph import DecisionEngine
from ai_engine.context.builder import ContextBuilder


def test_context_builder():
    """Test context builder."""
    builder = ContextBuilder()
    
    prices = [100, 101, 102, 103, 104]
    volumes = [1000, 1100, 1050, 1200, 1150]
    
    context = builder.build_context(
        symbol="BTC/USD",
        prices=prices,
        volumes=volumes,
    )
    
    assert context.symbol == "BTC/USD"
    assert context.market is not None
    assert context.ml is not None
    assert context.sentiment is not None


def test_decision_engine():
    """Test decision engine workflow."""
    engine = DecisionEngine(use_simple_graph=True)
    
    prices = [100, 101, 102, 103, 104, 105, 104, 103, 102, 103]
    volumes = [1000] * len(prices)
    
    decision = engine.decide(
        symbol="BTC/USD",
        prices=prices,
        volumes=volumes,
    )
    
    assert decision is not None
    assert "action" in decision
    assert "confidence" in decision
    assert decision["action"] in ["buy", "sell", "hold"]
    assert 0.0 <= decision["confidence"] <= 1.0


def test_decision_engine_with_rules():
    """Test decision engine with user rules."""
    engine = DecisionEngine(use_simple_graph=True)
    
    prices = [100, 101, 102, 103, 104]
    volumes = [1000] * len(prices)
    
    rules = [
        {
            "name": "Buy on uptrend",
            "conditions": [
                {"field": "market.trend", "operator": "eq", "value": "bullish"}
            ],
            "action": "buy",
        }
    ]
    
    decision = engine.decide(
        symbol="BTC/USD",
        prices=prices,
        volumes=volumes,
        rules=rules,
    )
    
    assert decision is not None
    assert "action" in decision
