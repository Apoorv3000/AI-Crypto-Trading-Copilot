"""ML subgraph schema - Pydantic models for ML predictions."""

from typing import Optional
from pydantic import BaseModel, Field


class MLWorkerOutput(BaseModel):
    """Output from ML worker (deterministic computation)."""
    
    predicted_direction: str = Field(description="Predicted price direction: up/down/neutral")
    direction_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in direction")
    
    predicted_volatility: str = Field(description="Predicted volatility: low/medium/high")
    volatility_score: float = Field(ge=0.0, le=1.0, description="Volatility score")
    
    prediction_quality: str = Field(description="Overall prediction quality: high/medium/low")


class MLEvaluation(BaseModel):
    """Evaluation of ML worker output by LLM."""
    
    is_valid: bool = Field(description="Whether the ML predictions are valid")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the predictions")
    
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Quality score based on prediction confidence and clarity"
    )
    
    issues: list[str] = Field(
        default_factory=list,
        description="Any issues or concerns found"
    )
    
    summary: str = Field(description="Brief summary of ML predictions")
    recommendation: str = Field(
        description="Evaluator's recommendation based on ML output"
    )


class MLSubgraphState(BaseModel):
    """State for ML subgraph."""
    
    # Input
    symbol: str
    prices: list[float]
    volumes: list[float]
    
    # Worker output
    worker_output: Optional[MLWorkerOutput] = None
    
    # Evaluator output
    evaluation: Optional[MLEvaluation] = None
    
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
