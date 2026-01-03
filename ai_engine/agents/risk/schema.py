"""Risk subgraph schema - Pydantic models for risk analysis."""

from typing import Optional
from pydantic import BaseModel, Field


class RiskWorkerOutput(BaseModel):
    """Output from risk worker (deterministic computation)."""
    
    stop_loss_check: bool = Field(description="Whether stop loss constraints are met")
    stop_loss_message: str = Field(description="Stop loss validation message")
    
    position_size_check: bool = Field(description="Whether position size is acceptable")
    position_size_message: str = Field(description="Position size validation message")
    
    exposure_check: bool = Field(description="Whether total exposure is acceptable")
    exposure_message: str = Field(description="Exposure validation message")
    
    all_checks_passed: bool = Field(description="Whether all risk checks passed")
    risk_level: str = Field(description="Overall risk level: low/medium/high")


class RiskEvaluation(BaseModel):
    """Evaluation of risk worker output by LLM."""
    
    is_valid: bool = Field(description="Whether the risk analysis is valid")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")
    
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Quality score based on risk validation thoroughness"
    )
    
    issues: list[str] = Field(
        default_factory=list,
        description="Any risk issues or concerns found"
    )
    
    summary: str = Field(description="Brief summary of risk conditions")
    recommendation: str = Field(
        description="Evaluator's recommendation based on risk analysis"
    )


class RiskSubgraphState(BaseModel):
    """State for risk subgraph."""
    
    # Input
    symbol: str
    current_price: float
    proposed_action: str = "buy"  # buy/sell/hold
    proposed_quantity: int = 1
    
    # Optional context
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Worker output
    worker_output: Optional[RiskWorkerOutput] = None
    
    # Evaluator output
    evaluation: Optional[RiskEvaluation] = None
    
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
