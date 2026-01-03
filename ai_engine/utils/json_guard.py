"""JSON validation and enforcement utilities.

Ensures all LLM outputs conform to expected schemas.
"""

from typing import Dict, Any, Optional
import json
from jsonschema import validate, ValidationError


def validate_json_output(
    data: Dict[str, Any],
    schema: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """Validate JSON data against a schema.
    
    Args:
        data: JSON data to validate
        schema: JSON schema
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)


def enforce_json_schema(
    data: Dict[str, Any],
    required_fields: list[str],
    defaults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Enforce required fields in JSON data, filling with defaults if missing.
    
    Args:
        data: Input JSON data
        required_fields: List of required field names
        defaults: Default values for missing fields
        
    Returns:
        JSON data with all required fields
    """
    if defaults is None:
        defaults = {}
    
    result = data.copy()
    
    for field in required_fields:
        if field not in result or result[field] is None:
            result[field] = defaults.get(field, None)
    
    return result


def get_decision_schema() -> Dict[str, Any]:
    """Get the JSON schema for final trading decisions.
    
    Returns:
        JSON schema for decision output
    """
    return {
        "type": "object",
        "required": ["action", "confidence", "reasoning", "timestamp"],
        "properties": {
            "action": {
                "type": "string",
                "enum": ["buy", "sell", "hold"]
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "reasoning": {
                "type": "string"
            },
            "position_size": {
                "type": "number",
                "minimum": 0.0
            },
            "stop_loss": {
                "type": "number",
                "minimum": 0.0
            },
            "take_profit": {
                "type": "number",
                "minimum": 0.0
            },
            "risk_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "timestamp": {
                "type": "string"
            },
            "signals": {
                "type": "object"
            }
        }
    }


def sanitize_decision_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate a trading decision output.
    
    Ensures the decision is safe for execution by enforcing required fields
    and validating data types.
    
    Args:
        data: Raw decision data
        
    Returns:
        Sanitized decision data
    """
    from datetime import datetime
    
    required_fields = ["action", "confidence", "reasoning", "timestamp"]
    defaults = {
        "action": "hold",
        "confidence": 0.0,
        "reasoning": "No reasoning provided",
        "timestamp": datetime.utcnow().isoformat(),
        "position_size": 0.0,
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "risk_score": 0.5,
        "signals": {}
    }
    
    # Enforce required fields
    sanitized = enforce_json_schema(data, required_fields, defaults)
    
    # Validate action
    valid_actions = ["buy", "sell", "hold"]
    if sanitized["action"] not in valid_actions:
        sanitized["action"] = "hold"
    
    # Validate confidence
    try:
        confidence = float(sanitized["confidence"])
        sanitized["confidence"] = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        sanitized["confidence"] = 0.0
    
    # Validate numeric fields
    numeric_fields = ["position_size", "stop_loss", "take_profit", "risk_score"]
    for field in numeric_fields:
        try:
            sanitized[field] = float(sanitized.get(field, defaults[field]))
        except (ValueError, TypeError):
            sanitized[field] = defaults[field]
    
    return sanitized
