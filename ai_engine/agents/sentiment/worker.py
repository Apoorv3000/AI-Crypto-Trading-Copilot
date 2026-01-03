"""Sentiment worker - deterministic sentiment analysis."""

from ...tools.sentiment import get_sentiment_analysis
from ...utils.logger import get_logger
from .schema import SentimentSubgraphState, SentimentWorkerOutput

logger = get_logger(__name__)


def sentiment_worker(state: SentimentSubgraphState) -> SentimentSubgraphState:
    """Execute deterministic sentiment analysis.
    
    Single responsibility: Gather sentiment data from sources.
    No LLM calls, no business logic, just data aggregation.
    
    On retry: Logs evaluator feedback but worker is deterministic so output is same.
    In a real system, worker could adjust sources or parameters.
    
    Args:
        state: Current subgraph state with symbol
        
    Returns:
        Updated state with worker_output populated
    """
    try:
        logger.info(f"Sentiment worker analyzing {state.symbol}")
        
        # If this is a retry, log the evaluator feedback
        if state.retry_count > 0:
            logger.warning(
                f"Sentiment worker retry attempt {state.retry_count}/{state.max_retries} for {state.symbol}. "
                f"Evaluator feedback: {state.evaluator_feedback}"
            )
        
        # Get sentiment data (deterministic - calls external APIs/mocks)
        sentiment_data = get_sentiment_analysis(state.symbol)
        
        # Extract nested data
        social = sentiment_data.get("social_sentiment", {})
        news = sentiment_data.get("news_sentiment", {})
        
        # Create structured output
        worker_output = SentimentWorkerOutput(
            social_sentiment=(social.get("twitter_sentiment", 0) + social.get("reddit_sentiment", 0)) / 2,
            social_volume=social.get("mentions_24h", 0),  # Fixed: use mentions_24h from CoinGecko
            news_sentiment=news.get("news_sentiment", 0),
            news_count=news.get("article_count_24h", 0),  # Fixed: use article_count_24h
            market_sentiment=sentiment_data.get("market_sentiment", {}).get("fear_greed_index", 50) / 100.0,
            overall_sentiment=sentiment_data.get("aggregate_sentiment", 0),
            sentiment_signal=sentiment_data.get("sentiment_signal", "neutral"),
        )
        
        logger.info(
            f"Sentiment worker completed: overall={worker_output.overall_sentiment:.2f}, "
            f"signal={worker_output.sentiment_signal}"
        )
        
        return SentimentSubgraphState(
            symbol=state.symbol,
            worker_output=worker_output,
            evaluation=state.evaluation,
            completed=False,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Sentiment worker error: {e}", exc_info=True)
        return SentimentSubgraphState(
            symbol=state.symbol,
            worker_output=None,
            evaluation=None,
            completed=True,
            error=f"Sentiment worker failed: {str(e)}",
        )
