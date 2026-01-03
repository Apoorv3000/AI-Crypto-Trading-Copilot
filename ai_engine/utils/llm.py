"""LLM wrapper using LangChain.

Provides a unified interface for LLM interactions.
"""

from typing import Dict, Any, Optional
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


def get_llm(
    model: str = "claude-3-5-sonnet-20240620",
    temperature: float = 0.1,
    **kwargs
) -> ChatAnthropic:
    """Get LangChain LLM instance.
    
    Args:
        model: Model name (default: claude-3-5-sonnet-20240620)
        temperature: Sampling temperature
        **kwargs: Additional model parameters
        
    Returns:
        LangChain LLM instance
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    llm = ChatAnthropic(
        model=model,
        temperature=temperature,
        anthropic_api_key=api_key,
        **kwargs
    )
    
    return llm


def llm_call(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20240620",
    temperature: float = 0.1,
    **kwargs
) -> str:
    """Make a simple LLM call with LangChain.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        model: Model name
        temperature: Sampling temperature
        **kwargs: Additional parameters
        
    Returns:
        LLM response as string
    """
    try:
        llm = get_llm(model=model, temperature=temperature, **kwargs)
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = llm.invoke(messages)
        return response.content
    
    except Exception as e:
        # Fallback for development/testing
        return f"{{'error': 'LLM call failed: {str(e)}', 'mock': 'true'}}"


def llm_call_structured(
    prompt: str,
    system_prompt: Optional[str] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    model: str = "claude-3-5-sonnet-20240620",
    temperature: float = 0.1,
    **kwargs
) -> Dict[str, Any]:
    """Make an LLM call expecting structured JSON output.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        output_schema: Expected output schema
        model: Model name
        temperature: Sampling temperature
        **kwargs: Additional parameters
        
    Returns:
        Parsed JSON response
    """
    import json
    
    # Add JSON instruction to prompt
    json_instruction = "\n\nYou MUST respond with valid JSON only. No other text."
    if output_schema:
        json_instruction += f"\n\nExpected schema: {json.dumps(output_schema, indent=2)}"
    
    full_prompt = prompt + json_instruction
    
    response = llm_call(
        full_prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        **kwargs
    )
    
    # Try to parse JSON
    try:
        # Extract JSON from response (handle markdown code blocks)
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Return error structure
        return {
            "error": "Failed to parse JSON response",
            "raw_response": response,
            "action": "hold",
            "confidence": 0.0,
        }
