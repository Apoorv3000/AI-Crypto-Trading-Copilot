"""Risk management tool.

Provides risk checks including stop loss, position limits, and exposure constraints.
This is a deterministic tool with NO LLM usage.
"""

from typing import Dict, Any, Optional


def check_stop_loss(
    current_price: float,
    entry_price: float,
    stop_loss_pct: float
) -> Dict[str, Any]:
    """Check if stop loss is triggered.
    
    Args:
        current_price: Current market price
        entry_price: Position entry price
        stop_loss_pct: Stop loss percentage (e.g., 0.05 for 5%)
        
    Returns:
        Stop loss check result
    """
    loss_pct = (entry_price - current_price) / entry_price
    triggered = loss_pct >= stop_loss_pct
    
    return {
        "triggered": triggered,
        "current_loss_pct": loss_pct * 100,
        "stop_loss_pct": stop_loss_pct * 100,
        "action": "close_position" if triggered else "hold",
    }


def check_position_size(
    proposed_size: float,
    account_balance: float,
    max_position_pct: float = 0.1
) -> Dict[str, Any]:
    """Check if position size is within limits.
    
    Args:
        proposed_size: Proposed position size (in USD)
        account_balance: Total account balance
        max_position_pct: Maximum position size as % of balance
        
    Returns:
        Position size check result
    """
    max_allowed = account_balance * max_position_pct
    is_valid = proposed_size <= max_allowed
    
    return {
        "is_valid": is_valid,
        "proposed_size": proposed_size,
        "max_allowed": max_allowed,
        "size_pct": (proposed_size / account_balance * 100) if account_balance > 0 else 0,
        "action": "proceed" if is_valid else "reduce_size",
    }


def check_exposure_limits(
    current_positions: Dict[str, float],
    account_balance: float,
    max_total_exposure: float = 0.5
) -> Dict[str, Any]:
    """Check total portfolio exposure.
    
    Args:
        current_positions: Dictionary of symbol -> position value
        account_balance: Total account balance
        max_total_exposure: Maximum total exposure as % of balance
        
    Returns:
        Exposure check result
    """
    total_exposure = sum(current_positions.values())
    exposure_pct = total_exposure / account_balance if account_balance > 0 else 0
    is_valid = exposure_pct <= max_total_exposure
    
    return {
        "is_valid": is_valid,
        "total_exposure": total_exposure,
        "exposure_pct": exposure_pct * 100,
        "max_exposure_pct": max_total_exposure * 100,
        "action": "proceed" if is_valid else "reduce_exposure",
    }


def check_volatility_limit(
    volatility: float,
    max_volatility: float = 0.05
) -> Dict[str, Any]:
    """Check if market volatility is within acceptable limits.
    
    Args:
        volatility: Current volatility measure
        max_volatility: Maximum acceptable volatility
        
    Returns:
        Volatility check result
    """
    is_valid = volatility <= max_volatility
    
    return {
        "is_valid": is_valid,
        "current_volatility": volatility * 100,
        "max_volatility": max_volatility * 100,
        "action": "proceed" if is_valid else "reduce_size_or_avoid",
    }


def check_risk_constraints(
    symbol: str,
    proposed_action: str,
    proposed_size: float,
    current_price: float,
    account_balance: float,
    current_positions: Dict[str, float] = None,
    entry_price: Optional[float] = None,
    volatility: float = 0.02,
    risk_params: Optional[Dict[str, float]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Perform comprehensive risk checks for a proposed trading action.
    
    This is a deterministic tool that enforces risk management rules
    without using any LLM.
    
    Args:
        symbol: Trading symbol
        proposed_action: Proposed action ('buy', 'sell', 'hold')
        proposed_size: Proposed position size (in USD)
        current_price: Current market price
        account_balance: Total account balance
        current_positions: Dictionary of current positions
        entry_price: Entry price (for stop loss check)
        volatility: Current market volatility
        risk_params: Optional risk parameters override
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing risk check results
    """
    if current_positions is None:
        current_positions = {}
    
    if risk_params is None:
        risk_params = {
            "stop_loss_pct": 0.05,  # 5%
            "max_position_pct": 0.10,  # 10%
            "max_total_exposure": 0.50,  # 50%
            "max_volatility": 0.05,  # 5%
        }
    
    checks = {
        "symbol": symbol,
        "proposed_action": proposed_action,
        "all_checks_passed": True,
        "warnings": [],
        "blockers": [],
    }
    
    # Position size check
    if proposed_action == "buy":
        size_check = check_position_size(
            proposed_size,
            account_balance,
            risk_params.get("max_position_pct", 0.1)
        )
        checks["position_size_check"] = size_check
        
        if not size_check["is_valid"]:
            checks["all_checks_passed"] = False
            checks["blockers"].append("Position size exceeds limit")
    
    # Exposure check
    exposure_check = check_exposure_limits(
        current_positions,
        account_balance,
        risk_params.get("max_total_exposure", 0.5)
    )
    checks["exposure_check"] = exposure_check
    
    if not exposure_check["is_valid"] and proposed_action == "buy":
        checks["all_checks_passed"] = False
        checks["blockers"].append("Total exposure exceeds limit")
    
    # Volatility check
    vol_check = check_volatility_limit(
        volatility,
        risk_params.get("max_volatility", 0.05)
    )
    checks["volatility_check"] = vol_check
    
    if not vol_check["is_valid"]:
        checks["warnings"].append("High volatility detected")
        if proposed_action == "buy":
            checks["blockers"].append("Volatility too high for new positions")
            checks["all_checks_passed"] = False
    
    # Stop loss check (if in position)
    if entry_price is not None and proposed_action != "buy":
        stop_loss_check = check_stop_loss(
            current_price,
            entry_price,
            risk_params.get("stop_loss_pct", 0.05)
        )
        checks["stop_loss_check"] = stop_loss_check
        
        if stop_loss_check["triggered"]:
            checks["warnings"].append("Stop loss triggered")
            checks["recommended_action"] = "close_position"
    
    # Final recommendation
    if checks["all_checks_passed"]:
        checks["risk_signal"] = "proceed"
    else:
        checks["risk_signal"] = "block"
    
    return checks
