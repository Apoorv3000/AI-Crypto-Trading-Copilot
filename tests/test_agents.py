"""Tests for the agents layer."""

import pytest
from ai_engine.context.schema import DecisionContext, MarketContext, MLContext
from ai_engine.agents import market_agent, ml_agent


def test_market_agent():
    """Test market agent."""
    # Create context with market data
    context = DecisionContext(
        symbol="BTC/USD",
        market=MarketContext(
            symbol="BTC/USD",
            current_price=50000.0,
            rsi=25.0,
            ema_20=49500.0,
            ema_50=49000.0,
            trend="bullish",
            volume_avg=1000.0,
            volume_current=1500.0,
            price_change_24h=2.5,
            rsi_signal="oversold",
        )
    )
    
    result = market_agent(context)
    
    assert result.market_agent_output is not None
    assert "signal" in result.market_agent_output
    assert "confidence" in result.market_agent_output
    assert result.market_agent_output["signal"] in ["bullish", "bearish", "neutral"]


def test_ml_agent():
    """Test ML agent."""
    context = DecisionContext(
        symbol="BTC/USD",
        ml=MLContext(
            symbol="BTC/USD",
            direction="up",
            direction_probability=0.75,
            confidence=0.8,
            volatility=0.02,
            volatility_regime="low",
            prediction_horizon="1h",
            ml_signal="strong",
        )
    )
    
    result = ml_agent(context)
    
    assert result.ml_agent_output is not None
    assert "signal" in result.ml_agent_output
    assert "confidence" in result.ml_agent_output
    assert result.ml_agent_output["signal"] in ["bullish", "bearish", "neutral"]
