"""Pydantic schemas for decision context.

Defines the structure of all context objects used in the decision engine.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MarketContext(BaseModel):
    """Market indicators context."""
    
    symbol: str
    current_price: float
    rsi: float
    ema_20: float
    ema_50: float
    trend: str
    volume_avg: float
    volume_current: float
    price_change_24h: float
    rsi_signal: str


class MLContext(BaseModel):
    """Machine learning predictions context."""
    
    symbol: str
    direction: str
    direction_probability: float
    confidence: float
    volatility: float
    volatility_regime: str
    prediction_horizon: str
    ml_signal: str


class SentimentContext(BaseModel):
    """Sentiment analysis context."""
    
    symbol: str
    aggregate_sentiment: float
    sentiment_label: str
    social_sentiment: Dict[str, Any]
    news_sentiment: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    sentiment_signal: str


class RulesContext(BaseModel):
    """User-defined rules evaluation context."""
    
    rules_evaluated: int
    rules_matched: int
    matched_rules: List[Dict[str, Any]]
    recommended_action: Optional[str]
    all_results: List[Dict[str, Any]]


class RiskContext(BaseModel):
    """Risk management context."""
    
    symbol: str
    proposed_action: str
    all_checks_passed: bool
    warnings: List[str]
    blockers: List[str]
    risk_signal: str
    position_size_check: Optional[Dict[str, Any]] = None
    exposure_check: Optional[Dict[str, Any]] = None
    volatility_check: Optional[Dict[str, Any]] = None
    stop_loss_check: Optional[Dict[str, Any]] = None


class HistoryContext(BaseModel):
    """Historical decisions and performance context."""
    
    recent_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    win_rate: float = 0.0
    total_trades: int = 0
    avg_return: float = 0.0
    last_action: Optional[str] = None


class DecisionContext(BaseModel):
    """Complete decision context combining all data sources.
    
    This is the main context object passed through the LangGraph workflow.
    """
    
    # Input parameters
    symbol: str
    request_id: str = Field(default="")
    prices: List[float] = Field(default_factory=list)
    volumes: List[float] = Field(default_factory=list)
    user_request: Optional[str] = None
    
    # Supervisor output
    supervisor_plan: Optional[Dict[str, Any]] = None
    trading_rules: List[str] = Field(default_factory=list)
    
    # Tool outputs (legacy, for backward compatibility)
    market: Optional[MarketContext] = None
    ml: Optional[MLContext] = None
    sentiment: Optional[SentimentContext] = None
    rules: Optional[RulesContext] = None
    risk: Optional[RiskContext] = None
    history: Optional[HistoryContext] = None
    
    # New: Context objects for compatibility
    market_context: Optional[MarketContext] = None
    ml_context: Optional[MLContext] = None
    sentiment_context: Optional[SentimentContext] = None
    rules_context: Optional[RulesContext] = None
    risk_context: Optional[RiskContext] = None
    history_context: Optional[HistoryContext] = None
    
    # Agent outputs (from subgraphs)
    market_agent_output: Optional[Dict[str, Any]] = None
    ml_agent_output: Optional[Dict[str, Any]] = None
    sentiment_agent_output: Optional[Dict[str, Any]] = None
    risk_agent_output: Optional[Dict[str, Any]] = None
    decision_agent_output: Optional[Dict[str, Any]] = None
    
    # Final decision
    final_decision: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    class Config:
        arbitrary_types_allowed = True
