"""Machine Learning predictions tool.

Provides ML-based predictions for price direction, volatility, and confidence.
This is a deterministic tool with NO LLM usage.
"""

from typing import Dict, Any, List
import numpy as np


def predict_price_direction(
    prices: List[float],
    features: Dict[str, Any]
) -> Dict[str, float]:
    """Predict price direction using ML model (stub implementation).
    
    In production, this would load a trained model and make predictions.
    For now, returns a simple heuristic-based prediction.
    
    Args:
        prices: Historical price data
        features: Additional features for prediction
        
    Returns:
        Dictionary with direction probabilities
    """
    if len(prices) < 10:
        return {
            "up_probability": 0.5,
            "down_probability": 0.5,
            "confidence": 0.3
        }
    
    # Simple momentum-based prediction (placeholder)
    recent_change = (prices[-1] - prices[-5]) / prices[-5]
    
    if recent_change > 0.02:
        up_prob = 0.65
    elif recent_change < -0.02:
        up_prob = 0.35
    else:
        up_prob = 0.5
    
    return {
        "up_probability": up_prob,
        "down_probability": 1 - up_prob,
        "confidence": min(abs(recent_change) * 10, 0.9)
    }


def predict_volatility(prices: List[float]) -> float:
    """Predict expected volatility.
    
    Args:
        prices: Historical price data
        
    Returns:
        Volatility estimate (standard deviation of returns)
    """
    if len(prices) < 2:
        return 0.02  # Default 2% volatility
    
    returns = np.diff(prices) / prices[:-1]
    volatility = float(np.std(returns))
    
    return volatility


def get_ml_predictions(
    symbol: str,
    prices: List[float],
    market_data: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Get ML-based predictions for trading decisions.
    
    This is a deterministic tool that uses ML models (or heuristics)
    without using any LLM.
    
    Args:
        symbol: Trading symbol
        prices: Historical price data
        market_data: Market indicators and data
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing ML predictions
    """
    direction_pred = predict_price_direction(prices, market_data)
    volatility = predict_volatility(prices)
    
    predictions = {
        "symbol": symbol,
        "direction": "up" if direction_pred["up_probability"] > 0.5 else "down",
        "direction_probability": max(direction_pred["up_probability"], direction_pred["down_probability"]),
        "confidence": direction_pred["confidence"],
        "volatility": volatility,
        "volatility_regime": "high" if volatility > 0.03 else "low" if volatility < 0.01 else "medium",
        "prediction_horizon": "1h",
    }
    
    # Add recommendation based on confidence
    if predictions["confidence"] > 0.7:
        predictions["ml_signal"] = "strong"
    elif predictions["confidence"] > 0.5:
        predictions["ml_signal"] = "moderate"
    else:
        predictions["ml_signal"] = "weak"
    
    return predictions
