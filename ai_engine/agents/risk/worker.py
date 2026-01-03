"""Risk worker - deterministic risk validation."""

from ...tools.risk import check_risk_constraints
from ...utils.logger import get_logger
from .schema import RiskSubgraphState, RiskWorkerOutput

logger = get_logger(__name__)


def risk_worker(state: RiskSubgraphState) -> RiskSubgraphState:
    """Execute deterministic risk validation.
    
    Single responsibility: Check risk constraints.
    No LLM calls, no business logic, just validation rules.
    
    On retry: Logs evaluator feedback but worker is deterministic so output is same.
    In a real system, worker could adjust thresholds or add more checks.
    
    Args:
        state: Current subgraph state with risk parameters
        
    Returns:
        Updated state with worker_output populated
    """
    try:
        logger.info(f"Risk worker validating {state.symbol}")
        
        # If this is a retry, log the evaluator feedback
        if state.retry_count > 0:
            logger.warning(
                f"Risk worker retry attempt {state.retry_count}/{state.max_retries} for {state.symbol}. "
                f"Evaluator feedback: {state.evaluator_feedback}"
            )
        
        # Check all risk constraints (deterministic)
        risk_checks = check_risk_constraints(
            symbol=state.symbol,
            proposed_action=state.proposed_action,
            proposed_size=float(state.proposed_quantity * state.current_price),
            current_price=state.current_price,
            account_balance=100000.0,  # Default account balance
            entry_price=state.stop_loss,
        )
        
        # Extract check results
        position_check = risk_checks.get("position_size_check", {})
        exposure_check = risk_checks.get("exposure_check", {})
        stop_loss_check = risk_checks.get("stop_loss_check", {})
        
        # Determine risk level
        if not risk_checks["all_checks_passed"]:
            risk_level = "high"
        elif risk_checks.get("warnings"):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Create structured output
        worker_output = RiskWorkerOutput(
            stop_loss_check=stop_loss_check.get("is_valid", True) if stop_loss_check else True,
            stop_loss_message=stop_loss_check.get("message", "No stop loss check") if stop_loss_check else "No stop loss check",
            position_size_check=position_check.get("is_valid", True),
            position_size_message=position_check.get("message", "Position size OK"),
            exposure_check=exposure_check.get("is_valid", True),
            exposure_message=exposure_check.get("message", "Exposure OK"),
            all_checks_passed=risk_checks["all_checks_passed"],
            risk_level=risk_level,
        )
        
        logger.info(
            f"Risk worker completed: checks_passed={worker_output.all_checks_passed}, "
            f"risk_level={worker_output.risk_level}"
        )
        
        return RiskSubgraphState(
            symbol=state.symbol,
            current_price=state.current_price,
            proposed_action=state.proposed_action,
            proposed_quantity=state.proposed_quantity,
            stop_loss=state.stop_loss,
            take_profit=state.take_profit,
            worker_output=worker_output,
            evaluation=state.evaluation,
            completed=False,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Risk worker error: {e}", exc_info=True)
        return RiskSubgraphState(
            symbol=state.symbol,
            current_price=state.current_price,
            proposed_action=state.proposed_action,
            proposed_quantity=state.proposed_quantity,
            stop_loss=state.stop_loss,
            take_profit=state.take_profit,
            worker_output=None,
            evaluation=None,
            completed=True,
            error=f"Risk worker failed: {str(e)}",
        )
