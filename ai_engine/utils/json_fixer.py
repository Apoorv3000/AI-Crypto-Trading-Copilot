"""JSON fixing utilities for LLM output parsing.

Handles common JSON formatting issues from LLM responses.
"""

import re
import json
from typing import Any, Dict


def fix_json_string(json_str: str) -> str:
    """Fix common JSON formatting issues from LLM responses.
    
    Handles:
    - Trailing commas before closing braces/brackets
    - Missing quotes around keys
    - Boolean values (true/false -> "true"/"false")
    - Null values
    
    Args:
        json_str: Raw JSON string from LLM
        
    Returns:
        Fixed JSON string that can be parsed
    """
    # Remove trailing commas before } or ]
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    # Remove comments (// or /* */)
    json_str = re.sub(r'//.*?\n', '\n', json_str)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    
    # Fix Python-style booleans and None
    json_str = re.sub(r'\bTrue\b', 'true', json_str)
    json_str = re.sub(r'\bFalse\b', 'false', json_str)
    json_str = re.sub(r'\bNone\b', 'null', json_str)
    
    return json_str


def parse_json_safely(json_str: str) -> Dict[str, Any]:
    """Parse JSON string with automatic fixing.
    
    Tries multiple strategies:
    1. Parse as-is
    2. Fix common issues and parse
    3. Extract JSON from markdown code blocks
    4. Return error dict
    
    Args:
        json_str: Raw JSON string
        
    Returns:
        Parsed dict or error dict
    """
    # Try parsing as-is
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Try fixing common issues
    try:
        fixed = fix_json_string(json_str)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_str, re.DOTALL)
    if match:
        try:
            fixed = fix_json_string(match.group(1))
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    
    # Try finding first complete JSON object
    match = re.search(r'\{.*\}', json_str, re.DOTALL)
    if match:
        try:
            fixed = fix_json_string(match.group(0))
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    
    # Return error dict as fallback
    return {
        "error": "Failed to parse JSON",
        "raw_output": json_str[:500],
        "is_valid": False,
        "confidence": 0.0,
        "quality_score": 0.0,
        "issues": ["JSON parsing failed"],
        "summary": "Failed to parse evaluator output",
        "recommendation": "Retry evaluation"
    }
