"""Tests for the tools layer."""

import pytest
from ai_engine.tools import (
    get_market_indicators,
    get_ml_predictions,
    get_sentiment_analysis,
    evaluate_rules,
    check_risk_constraints,
)


def test_market_indicators():
    """Test market indicators tool."""
    prices = [100, 101, 102, 103, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104]
    volumes = [1000] * len(prices)
    
    result = get_market_indicators("BTC/USD", prices, volumes)
    
    assert result["symbol"] == "BTC/USD"
    assert "rsi" in result
    assert "ema_20" in result
    assert "trend" in result
    assert result["current_price"] == 104


def test_ml_predictions():
    """Test ML predictions tool."""
    prices = [100, 101, 102, 103, 104, 105]
    market_data = {"rsi": 50, "trend": "bullish"}
    
    result = get_ml_predictions("BTC/USD", prices, market_data)
    
    assert result["symbol"] == "BTC/USD"
    assert "direction" in result
    assert "confidence" in result
    assert result["direction"] in ["up", "down"]


def test_sentiment_analysis():
    """Test sentiment analysis tool."""
    result = get_sentiment_analysis("BTC/USD")
    
    assert result["symbol"] == "BTC/USD"
    assert "aggregate_sentiment" in result
    assert "sentiment_label" in result
    assert result["sentiment_label"] in ["positive", "negative", "neutral"]


def test_evaluate_rules():
    """Test rules evaluation tool."""
    rules = [
        {
            "name": "RSI Oversold",
            "conditions": [
                {"field": "market.rsi", "operator": "lt", "value": 30}
            ],
            "action": "buy",
            "logic": "AND",
        }
    ]
    
    context = {
        "market": {"rsi": 25}
    }
    
    result = evaluate_rules(rules, context)
    
    assert result["rules_evaluated"] == 1
    assert result["rules_matched"] == 1
    assert result["recommended_action"] == "buy"


def test_risk_constraints():
    """Test risk constraints tool."""
    result = check_risk_constraints(
        symbol="BTC/USD",
        proposed_action="buy",
        proposed_size=1000.0,
        current_price=50000.0,
        account_balance=10000.0,
        volatility=0.02,
    )
    
    assert result["symbol"] == "BTC/USD"
    assert "all_checks_passed" in result
    assert "risk_signal" in result
    assert result["risk_signal"] in ["proceed", "block"]
