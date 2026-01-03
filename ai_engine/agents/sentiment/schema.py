"""Sentiment subgraph schema - Pydantic models for sentiment analysis."""

from typing import Optional
from pydantic import BaseModel, Field


class SentimentWorkerOutput(BaseModel):
    """Output from sentiment worker (deterministic computation)."""
    
    social_sentiment: float = Field(ge=-1.0, le=1.0, description="Social media sentiment")
    social_volume: int = Field(description="Number of social mentions")
    
    news_sentiment: float = Field(ge=-1.0, le=1.0, description="News sentiment")
    news_count: int = Field(description="Number of news articles")
    
    market_sentiment: float = Field(ge=-1.0, le=1.0, description="Market mood sentiment")
    
    overall_sentiment: float = Field(ge=-1.0, le=1.0, description="Weighted average sentiment")
    sentiment_signal: str = Field(description="Sentiment signal: bullish/bearish/neutral")


class SentimentEvaluation(BaseModel):
    """Evaluation of sentiment worker output by LLM."""
    
    is_valid: bool = Field(description="Whether the sentiment analysis is valid")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")
    
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Quality score based on data sources and consistency"
    )
    
    issues: list[str] = Field(
        default_factory=list,
        description="Any issues or concerns found"
    )
    
    summary: str = Field(description="Brief summary of sentiment conditions")
    recommendation: str = Field(
        description="Evaluator's recommendation based on sentiment"
    )


class SentimentSubgraphState(BaseModel):
    """State for sentiment subgraph."""
    
    # Input
    symbol: str
    
    # Worker output
    worker_output: Optional[SentimentWorkerOutput] = None
    
    # Evaluator output
    evaluation: Optional[SentimentEvaluation] = None
    
    # Retry mechanism
    retry_count: int = Field(default=0, description="Number of worker retry attempts")
    max_retries: int = Field(default=2, description="Maximum worker retry attempts")
    evaluator_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from evaluator for worker to address on retry"
    )
    
    # Combined output
    completed: bool = False
    error: Optional[str] = None
