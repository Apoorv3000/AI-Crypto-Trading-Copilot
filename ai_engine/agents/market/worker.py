"""Market worker - deterministic technical analysis."""

from ...tools.market import (
    calculate_rsi,
    calculate_ema,
    get_trend_direction,
    get_market_indicators,
)
from ...utils.logger import get_logger
from .schema import MarketSubgraphState, MarketWorkerOutput

logger = get_logger(__name__)


def market_worker(state: MarketSubgraphState) -> MarketSubgraphState:
    """Execute deterministic market analysis.
    
    Single responsibility: Calculate technical indicators.
    No LLM calls, no business logic, just pure computation.
    
    On retry: Logs evaluator feedback but worker is deterministic so output is same.
    In a real system, worker could adjust parameters or fetch fresh data.
    
    Args:
        state: Current subgraph state with symbol, prices, volumes
        
    Returns:
        Updated state with worker_output populated
    """
    try:
        logger.info(f"Market worker analyzing {state.symbol}")
        
        # If this is a retry, log the evaluator feedback
        if state.retry_count > 0:
            logger.warning(
                f"Market worker retry attempt {state.retry_count}/{state.max_retries} for {state.symbol}. "
                f"Evaluator feedback: {state.evaluator_feedback}"
            )
        
        # Get all indicators (deterministic)
        indicators = get_market_indicators(state.symbol, state.prices, state.volumes)
        
        # Determine EMA signal
        ema_20 = indicators.get("ema_20", 0)
        ema_50 = indicators.get("ema_50", 0)
        if ema_20 > ema_50:
            ema_signal = "bullish"
        elif ema_20 < ema_50:
            ema_signal = "bearish"
        else:
            ema_signal = "neutral"
        
        # Determine volume signal
        volume_current = indicators.get("volume_current", 0)
        volume_avg = indicators.get("volume_avg", 1)
        volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1.0
        
        if volume_ratio > 1.5:
            volume_signal = "high"
        elif volume_ratio < 0.5:
            volume_signal = "low"
        else:
            volume_signal = "normal"
        
        # Determine trend strength (based on price momentum)
        trend = indicators.get("trend", "sideways")
        price_change = abs(indicators.get("price_change_24h", 0))
        trend_strength = min(price_change / 10.0, 1.0)  # Normalize to 0-1
        
        # Create structured output
        worker_output = MarketWorkerOutput(
            rsi=indicators["rsi"],
            rsi_signal=indicators["rsi_signal"],
            ema_short=ema_20,
            ema_long=ema_50,
            ema_signal=ema_signal,
            volume_ratio=volume_ratio,
            volume_signal=volume_signal,
            trend_direction=trend,
            trend_strength=trend_strength,
        )
        
        logger.info(f"Market worker completed: trend={worker_output.trend_direction}, rsi={worker_output.rsi:.1f}")
        
        return MarketSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=worker_output,
            evaluation=state.evaluation,
            completed=False,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Market worker error: {e}", exc_info=True)
        return MarketSubgraphState(
            symbol=state.symbol,
            prices=state.prices,
            volumes=state.volumes,
            worker_output=None,
            evaluation=None,
            completed=True,
            error=f"Market worker failed: {str(e)}",
        )
