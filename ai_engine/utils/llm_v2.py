"""LLM utility - model-agnostic LLM support (Claude, GPT, Gemini)."""

import os
from typing import Literal, Optional

LLMProvider = Literal["anthropic", "openai", "google"]


def get_llm(
    temperature: float = 0.7,
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
):
    """Get a configured LLM instance (supports Claude, GPT, Gemini).
    
    Args:
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        provider: LLM provider - "anthropic", "openai", or "google"
                 If None, auto-detects from environment variables
        model: Specific model name (optional)
        
    Returns:
        Configured LLM instance
        
    Environment Variables:
        ANTHROPIC_API_KEY - For Claude models
        OPENAI_API_KEY - For GPT models
        GOOGLE_API_KEY - For Gemini models
    
    Examples:
        # Use Claude (default if ANTHROPIC_API_KEY is set)
        llm = get_llm(temperature=0.1)
        
        # Explicitly use GPT
        llm = get_llm(provider="openai", model="gpt-4-turbo-preview")
        
        # Use Gemini
        llm = get_llm(provider="google", model="gemini-pro")
    """
    # Auto-detect provider if not specified
    if provider is None:
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GOOGLE_API_KEY"):
            provider = "google"
        else:
            raise ValueError(
                "No LLM provider configured. Set one of: "
                "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
            )
    
    # Anthropic (Claude)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        return ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=temperature,
            anthropic_api_key=api_key,
        )
    
    # OpenAI (GPT)
    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. Run: poetry add langchain-openai"
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        return ChatOpenAI(
            model=model or "gpt-4-turbo-preview",
            temperature=temperature,
            openai_api_key=api_key,
        )
    
    # Google (Gemini)
    elif provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. Run: poetry add langchain-google-genai"
            )
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        return ChatGoogleGenerativeAI(
            model=model or "gemini-pro",
            temperature=temperature,
            google_api_key=api_key,
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use: anthropic, openai, or google")


class LLMConfig:
    """Per-agent LLM configuration.
    
    Allows different agents to use different models for cost/performance optimization.
    
    Examples:
        # Supervisor uses Claude for strong reasoning
        llm = get_llm(**LLMConfig.SUPERVISOR)
        
        # Evaluators could use cheaper Gemini
        llm = get_llm(**LLMConfig.EVALUATORS)
    """
    
    # Main supervisor - needs strong reasoning
    SUPERVISOR = {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.3,
    }
    
    # Router - needs fast, consistent decisions
    ROUTER = {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.0,
    }
    
    # Evaluators - can use cheaper models
    EVALUATORS = {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.0,
    }
    
    # Final aggregator - needs best reasoning
    AGGREGATOR = {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.1,
    }
