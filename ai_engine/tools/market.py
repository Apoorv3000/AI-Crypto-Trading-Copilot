"""Market indicators tool.

Provides technical analysis indicators like RSI, EMA, volume, and trend analysis.
This is a deterministic tool with NO LLM usage.
"""

from typing import Dict, Any, List
import numpy as np


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of historical prices
        period: RSI period (default 14)
        
    Returns:
        RSI value between 0 and 100
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral RSI if insufficient data
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def calculate_ema(prices: List[float], period: int = 20) -> float:
    """Calculate Exponential Moving Average (EMA).
    
    Args:
        prices: List of historical prices
        period: EMA period (default 20)
        
    Returns:
        EMA value
    """
    if len(prices) < period:
        return float(np.mean(prices))
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return float(ema)


def get_trend_direction(prices: List[float]) -> str:
    """Determine trend direction based on price history.
    
    Args:
        prices: List of historical prices
        
    Returns:
        Trend direction: 'bullish', 'bearish', or 'neutral'
    """
    if len(prices) < 3:
        return "neutral"
    
    short_ema = calculate_ema(prices[-10:], 5)
    long_ema = calculate_ema(prices[-20:], 10)
    
    if short_ema > long_ema * 1.01:
        return "bullish"
    elif short_ema < long_ema * 0.99:
        return "bearish"
    else:
        return "neutral"


def get_market_indicators(
    symbol: str,
    prices: List[float],
    volumes: List[float],
    **kwargs
) -> Dict[str, Any]:
    """Get comprehensive market indicators for a trading symbol.
    
    This is a deterministic tool that calculates technical indicators
    without using any LLM.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC/USD')
        prices: Historical price data
        volumes: Historical volume data
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing market indicators
    """
    current_price = prices[-1] if prices else 0.0
    
    indicators = {
        "symbol": symbol,
        "current_price": current_price,
        "rsi": calculate_rsi(prices),
        "ema_20": calculate_ema(prices, 20),
        "ema_50": calculate_ema(prices, 50),
        "trend": get_trend_direction(prices),
        "volume_avg": float(np.mean(volumes[-20:])) if volumes else 0.0,
        "volume_current": volumes[-1] if volumes else 0.0,
        "price_change_24h": ((prices[-1] - prices[-24]) / prices[-24] * 100) if len(prices) >= 24 else 0.0,
    }
    
    # Add interpretation
    if indicators["rsi"] > 70:
        indicators["rsi_signal"] = "overbought"
    elif indicators["rsi"] < 30:
        indicators["rsi_signal"] = "oversold"
    else:
        indicators["rsi_signal"] = "neutral"
    
    return indicators
