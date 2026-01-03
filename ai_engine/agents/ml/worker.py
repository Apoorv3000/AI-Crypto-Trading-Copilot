"""ML worker - deterministic ML predictions."""

from ...tools.ml import get_ml_predictions
from ...utils.logger import get_logger
from .schema import MLSubgraphState, MLWorkerOutput

logger = get_logger(__name__)


def ml_worker(state: MLSubgraphState) -> MLSubgraphState:
    """Execute deterministic ML predictions.
    
    Single responsibility: Generate ML-based predictions.
    No LLM calls, no business logic, just model inference.
    
    On retry: Logs evaluator feedback but worker is deterministic so output is same.
    In a real system, worker could use different model or parameters.
    
    Args:
        state: Current subgraph state with symbol, prices, volumes
        
    Returns:
        Updated state with worker_output populated
    """
    try:
        logger.info(f"ML worker predicting {state.symbol}")
        
        # If this is a retry, log the evaluator feedback
        if state.retry_count > 0:
            logger.warning(
                f"ML worker retry attempt {state.retry_count}/{state.max_retries} for {state.symbol}. "
                f"Evaluator feedback: {state.evaluator_feedback}"
            )
        
        # Get ML predictions (deterministic model inference)
        predictions = get_ml_predictions(
            symbol=state.symbol,
            prices=state.prices,
            market_data={"volumes": state.volumes}  # Minimal market data
        )
        
        # Create structured output
        worker_output = MLWorkerOutput(
            predicted_direction=predictions["direction"],
            direction_confidence=predictions["confidence"],
            predicted_volatility=predictions["volatility_regime"],
            volatility_score=predictions["volatility"],
            prediction_quality=predictions["ml_signal"],
        )
        
        logger.info(
            f"ML worker completed: direction={worker_output.predicted_direction}, "
            f"confidence={worker_output.direction_confidence:.2f}"
        )
        
        return MLSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=worker_output,
            evaluation=state.evaluation,
            completed=False,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"ML worker error: {e}", exc_info=True)
        return MLSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=None,
            evaluation=None,
            completed=True,
            error=f"ML worker failed: {str(e)}",
        )
