"""Risk subgraph builder - worker → evaluator workflow."""

from langgraph.graph import StateGraph, END

from ...utils.logger import get_logger
from .schema import RiskSubgraphState
from .worker import risk_worker
from .evaluator import risk_evaluator

logger = get_logger(__name__)


def should_retry_worker(state: RiskSubgraphState) -> str:
    """Decide if worker should retry based on evaluator feedback.
    
    Returns:
        'worker' if evaluation failed and retries remain
        'END' if evaluation passed or max retries reached
    """
    if not state.evaluation:
        return END
    
    if state.evaluation.is_valid:
        return END
    
    # Hard check: evaluator already incremented retry_count, so check if exceeded
    if state.retry_count > state.max_retries:
        error_msg = (
            f"\n{'='*80}\n"
            f"[USER ACTION REQUIRED] Risk validation FAILED for {state.symbol}\n"
            f"Max retries ({state.max_retries}) exhausted.\n"
            f"Issues: {', '.join(state.evaluation.issues)}\n"
            f"Feedback: {state.evaluator_feedback}\n"
            f"Worker output cannot fix these issues automatically.\n"
            f"{'='*80}\n"
        )
        logger.error(error_msg)
        return END
    
    # Human-in-the-loop: Ask user if they want to retry
    print(f"\n{'='*70}")
    print(f"⚠️  RISK VALIDATION FAILED - {state.symbol}")
    print(f"{'='*70}")
    print(f"\n📊 Retry {state.retry_count}/{state.max_retries}")
    print(f"\n❌ Issues found:")
    for issue in state.evaluation.issues:
        print(f"   • {issue}")
    print(f"\n💡 Evaluator feedback: {state.evaluator_feedback}")
    print(f"\n{'='*70}")
    print("\nWhat would you like to do?")
    print("  [y] Retry with feedback")
    print("  [n] Skip and continue with current data")
    print("  [a] Abort entire decision")
    
    choice = input("\nYour choice (y/n/a): ").strip().lower()
    print(f"{'='*70}\n")
    
    if choice == 'a':
        logger.info("User aborted risk analysis")
        raise Exception("User aborted risk analysis")
    elif choice == 'n':
        logger.info("User skipped risk retry, continuing with current data")
        return END
    else:
        # Default to retry
        logger.info("User approved risk retry")
        return 'worker'
    
    logger.info(
        f"Risk worker retry {state.retry_count}/{state.max_retries} for {state.symbol}. "
        f"Feedback: {state.evaluation.issues}"
    )
    return "worker"


def create_risk_subgraph() -> StateGraph:
    """Create risk validation subgraph.
    
    Architecture:
        START → worker → evaluator → [conditional]
        If evaluator rejects: → worker (with feedback)
        Else: → END
        
    Worker: Deterministic risk checks
    Evaluator: LLM validation (LCEL)
    
    Returns:
        Compiled risk subgraph
    """
    logger.info("Creating risk subgraph")
    
    # Create graph
    graph = StateGraph(RiskSubgraphState)
    
    # Add nodes
    graph.add_node("worker", risk_worker)
    graph.add_node("evaluator", risk_evaluator)
    
    # Define flow
    graph.set_entry_point("worker")
    graph.add_edge("worker", "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        should_retry_worker,
        {"worker": "worker", END: END}
    )
    
    # Compile
    workflow = graph.compile()
    
    logger.info("Risk subgraph created successfully with retry logic")
    return workflow
