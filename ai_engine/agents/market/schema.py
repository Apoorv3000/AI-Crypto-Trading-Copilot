"""Market subgraph schema - Pydantic models for market analysis."""

from typing import Optional
from pydantic import BaseModel, Field


class MarketWorkerOutput(BaseModel):
    """Output from market worker (deterministic computation)."""
    
    rsi: float = Field(description="RSI indicator value (0-100)")
    rsi_signal: str = Field(description="RSI signal: oversold/neutral/overbought")
    
    ema_short: float = Field(description="Short-term EMA value")
    ema_long: float = Field(description="Long-term EMA value")
    ema_signal: str = Field(description="EMA signal: bullish/bearish/neutral")
    
    volume_ratio: float = Field(description="Current volume / average volume")
    volume_signal: str = Field(description="Volume signal: high/normal/low")
    
    trend_direction: str = Field(description="Overall trend: bullish/bearish/sideways")
    trend_strength: float = Field(description="Trend strength (0-1)")


class MarketEvaluation(BaseModel):
    """Evaluation of market worker output by LLM."""
    
    is_valid: bool = Field(description="Whether the market analysis is valid")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")
    
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Quality score based on indicator consistency"
    )
    
    issues: list[str] = Field(
        default_factory=list,
        description="Any issues or concerns found"
    )
    
    summary: str = Field(description="Brief summary of market conditions")
    recommendation: str = Field(
        description="Evaluator's recommendation based on technical analysis"
    )


class MarketSubgraphState(BaseModel):
    """State for market subgraph."""
    
    # Input
    symbol: str
    prices: list[float]
    volumes: list[float]
    
    # Worker output
    worker_output: Optional[MarketWorkerOutput] = None
    
    # Evaluator output
    evaluation: Optional[MarketEvaluation] = None
    
    # Retry mechanism
    retry_count: int = Field(default=0, description="Number of worker retry attempts")
    max_retries: int = Field(default=2, description="Maximum worker retry attempts")
    evaluator_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from evaluator for worker to address on retry"
    )
    
    # Combined output (for parent graph)
    completed: bool = False
    error: Optional[str] = None
