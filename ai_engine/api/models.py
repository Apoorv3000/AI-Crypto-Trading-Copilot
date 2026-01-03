"""Pydantic models for API requests and responses."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    """Request model for trading decision endpoint."""
    
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USD')")
    prices: List[float] = Field(..., description="Historical price data", min_items=1)
    volumes: List[float] = Field(..., description="Historical volume data", min_items=1)
    
    # Optional parameters
    rules: Optional[List[Dict[str, Any]]] = Field(default=None, description="User-defined trading rules")
    proposed_action: str = Field(default="hold", description="Proposed action to evaluate")
    proposed_size: float = Field(default=0.0, description="Proposed position size in USD")
    account_balance: float = Field(default=10000.0, description="Account balance in USD")
    current_positions: Optional[Dict[str, float]] = Field(default=None, description="Current positions")
    entry_price: Optional[float] = Field(default=None, description="Entry price for stop loss calculation")
    fear_greed_index: Optional[float] = Field(default=None, description="Fear & Greed index (0-100)")
    history: Optional[Dict[str, Any]] = Field(default=None, description="Historical performance data")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC/USD",
                "prices": [50000, 50100, 50200, 50300, 50250, 50400, 50500, 50450, 50600, 50700],
                "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500],
                "proposed_action": "buy",
                "proposed_size": 1000.0,
                "account_balance": 10000.0,
                "fear_greed_index": 65.0,
            }
        }


class DecisionResponse(BaseModel):
    """Response model for trading decision endpoint."""
    
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Trading action: buy, sell, or hold")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    
    # Optional fields
    position_size: float = Field(default=0.0, description="Recommended position size")
    stop_loss: float = Field(default=0.0, description="Recommended stop loss price")
    take_profit: float = Field(default=0.0, description="Recommended take profit price")
    risk_score: float = Field(default=0.5, description="Risk score (0.0-1.0)")
    
    # Metadata
    timestamp: str = Field(..., description="Decision timestamp (ISO format)")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    request_id: str = Field(default="", description="Request ID")
    signals: Dict[str, Any] = Field(default_factory=dict, description="Signal breakdown")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC/USD",
                "action": "buy",
                "confidence": 0.75,
                "reasoning": "Strong bullish signals from market indicators (RSI oversold, bullish trend) combined with positive ML prediction and sentiment.",
                "position_size": 1000.0,
                "stop_loss": 49500.0,
                "take_profit": 52000.0,
                "risk_score": 0.35,
                "timestamp": "2025-12-29T10:30:00Z",
                "processing_time_ms": 250.5,
                "request_id": "req_123456",
                "signals": {
                    "market": "bullish",
                    "ml": "bullish",
                    "sentiment": "positive",
                    "risk": "proceed"
                }
            }
        }
