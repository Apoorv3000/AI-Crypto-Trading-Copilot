"""API routes for the decision engine."""

from fastapi import APIRouter, HTTPException
from .models import DecisionRequest, DecisionResponse
from ..graph.engine import DecisionEngine
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize decision engine (singleton)
decision_engine = DecisionEngine(use_simple_graph=False)


@router.post("/decide", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest) -> DecisionResponse:
    """Make a trading decision based on input data.
    
    This endpoint:
    1. Accepts trading data (prices, volumes, rules, etc.)
    2. Runs the multi-agent LangGraph workflow
    3. Returns a structured trading decision
    
    Args:
        request: Decision request with market data and parameters
        
    Returns:
        Trading decision with action, confidence, and reasoning
    """
    logger.info(f"Received decision request for {request.symbol}")
    
    try:
        # Convert request to parameters
        params = request.dict()
        
        # Extract main parameters
        symbol = params.pop("symbol")
        prices = params.pop("prices")
        volumes = params.pop("volumes")
        
        # Execute decision workflow
        decision = await decision_engine.decide_async(
            symbol=symbol,
            prices=prices,
            volumes=volumes,
            **params
        )
        
        # Build response
        response = DecisionResponse(
            symbol=symbol,
            action=decision.get("action", "hold"),
            confidence=decision.get("confidence", 0.0),
            reasoning=decision.get("reasoning", "No reasoning provided"),
            position_size=decision.get("position_size", 0.0),
            stop_loss=decision.get("stop_loss", 0.0),
            take_profit=decision.get("take_profit", 0.0),
            risk_score=decision.get("risk_score", 0.5),
            timestamp=decision.get("timestamp", ""),
            processing_time_ms=decision.get("processing_time_ms", 0.0),
            signals=decision.get("signals", {}),
            request_id=decision.get("request_id", ""),
        )
        
        logger.info(f"Decision completed for {symbol}: {response.action}")
        return response
    
    except Exception as e:
        logger.error(f"Error processing decision request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing decision: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get engine status."""
    return {
        "status": "operational",
        "engine": "running",
        "graph_type": "simple" if decision_engine.use_simple_graph else "full",
    }
