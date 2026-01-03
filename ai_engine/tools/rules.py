"""Rules evaluation tool.

Evaluates user-defined trading rules and strategy configurations.
This is a deterministic tool with NO LLM usage.
"""

from typing import Dict, Any, List, Optional


def parse_rule_condition(
    condition: Dict[str, Any],
    context: Dict[str, Any]
) -> bool:
    """Parse and evaluate a single rule condition.
    
    Args:
        condition: Rule condition specification
        context: Current market/analysis context
        
    Returns:
        True if condition is met, False otherwise
    """
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")
    
    if not all([field, operator, value]):
        return False
    
    # Extract field value from context (support nested paths)
    current_value = context
    for key in field.split("."):
        if isinstance(current_value, dict):
            current_value = current_value.get(key)
        else:
            return False
    
    if current_value is None:
        return False
    
    # Evaluate condition
    try:
        if operator == "gt":
            return float(current_value) > float(value)
        elif operator == "lt":
            return float(current_value) < float(value)
        elif operator == "gte":
            return float(current_value) >= float(value)
        elif operator == "lte":
            return float(current_value) <= float(value)
        elif operator == "eq":
            return current_value == value
        elif operator == "neq":
            return current_value != value
        elif operator == "in":
            return current_value in value
        elif operator == "not_in":
            return current_value not in value
        else:
            return False
    except (ValueError, TypeError):
        return False


def evaluate_rule(rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single trading rule.
    
    Args:
        rule: Rule specification with conditions and actions
        context: Current market/analysis context
        
    Returns:
        Evaluation result with matched status and actions
    """
    conditions = rule.get("conditions", [])
    logic = rule.get("logic", "AND")  # AND or OR
    
    if not conditions:
        return {"matched": False, "rule_name": rule.get("name", "unknown")}
    
    # Evaluate all conditions
    results = [parse_rule_condition(cond, context) for cond in conditions]
    
    # Apply logic
    if logic == "AND":
        matched = all(results)
    elif logic == "OR":
        matched = any(results)
    else:
        matched = False
    
    return {
        "rule_name": rule.get("name", "unknown"),
        "matched": matched,
        "action": rule.get("action") if matched else None,
        "confidence": rule.get("confidence", 1.0) if matched else 0.0,
    }


def evaluate_rules(
    rules: List[Dict[str, Any]],
    context: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Evaluate all user-defined trading rules.
    
    This is a deterministic tool that evaluates structured rule configurations
    without using any LLM.
    
    Args:
        rules: List of rule specifications
        context: Current market/analysis context
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing rule evaluation results
    """
    if not rules:
        return {
            "rules_evaluated": 0,
            "rules_matched": 0,
            "matched_rules": [],
            "recommended_action": None,
        }
    
    results = [evaluate_rule(rule, context) for rule in rules]
    matched_results = [r for r in results if r["matched"]]
    
    # Determine recommended action
    recommended_action = None
    if matched_results:
        # Use the rule with highest confidence
        best_match = max(matched_results, key=lambda x: x["confidence"])
        recommended_action = best_match["action"]
    
    evaluation = {
        "rules_evaluated": len(results),
        "rules_matched": len(matched_results),
        "matched_rules": matched_results,
        "recommended_action": recommended_action,
        "all_results": results,
    }
    
    return evaluation
