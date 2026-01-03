"""Market subgraph builder - worker → evaluator workflow."""

from langgraph.graph import StateGraph, END

from ...utils.logger import get_logger
from .schema import MarketSubgraphState
from .worker import market_worker
from .evaluator import market_evaluator

logger = get_logger(__name__)


def should_retry_worker(state: MarketSubgraphState) -> str:
    """Decide if worker should retry based on evaluator feedback.
    
    Returns:
        'worker' if evaluation failed and retries remain
        'END' if evaluation passed or max retries reached
    """
    if not state.evaluation:
        return END
    
    # If evaluation is valid, we're done
    if state.evaluation.is_valid:
        return END
    
    # Hard check: evaluator already incremented retry_count, so check if exceeded
    if state.retry_count > state.max_retries:
        error_msg = (
            f"\n{'='*80}\n"
            f"[USER ACTION REQUIRED] Market validation FAILED for {state.symbol}\n"
            f"Max retries ({state.max_retries}) exhausted.\n"
            f"Issues: {', '.join(state.evaluation.issues)}\n"
            f"Feedback: {state.evaluator_feedback}\n"
            f"Worker output cannot fix these issues automatically.\n"
            f"{'='*80}\n"
        )
        logger.error(error_msg)
        return END
    
    # Retry with feedback
    logger.info(
        f"Market worker retry {state.retry_count}/{state.max_retries} for {state.symbol}. "
        f"Evaluator feedback: {state.evaluation.issues}"
    )
    return "worker"


def create_market_subgraph() -> StateGraph:
    """Create market analysis subgraph.
    
    Architecture:
        START → worker → evaluator → [conditional]
        If evaluator rejects (is_valid=False) and retry_count < max_retries:
            → worker (with feedback)
        Else:
            → END
        
    Worker: Deterministic technical analysis
    Evaluator: LLM validation (LCEL)
    
    Returns:
        Compiled market subgraph
    """
    logger.info("Creating market subgraph")
    
    # Create graph with MarketSubgraphState
    graph = StateGraph(MarketSubgraphState)
    
    # Add nodes
    graph.add_node("worker", market_worker)
    graph.add_node("evaluator", market_evaluator)
    
    # Define flow: worker → evaluator → conditional
    graph.set_entry_point("worker")
    graph.add_edge("worker", "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        should_retry_worker,
        {"worker": "worker", END: END}
    )
    
    # Compile
    workflow = graph.compile()
    
    logger.info("Market subgraph created successfully with retry logic")
    return workflow
