#!/usr/bin/env python3
"""
LLM Factory: Create LLM instances for different providers (OpenAI, Google Gemini)
"""
import os
from typing import Optional


def create_llm(model: str, temperature: float = 0.2, json_mode: bool = True, **kwargs):
    """
    Create an LLM instance based on the model name.

    Supports:
    - OpenAI models (gpt-4, gpt-5, etc.)
    - Google Gemini models (gemini-1.5-pro, gemini-2.0-flash, etc.)

    Args:
        model: Model identifier (e.g., "gpt-4-turbo", "gemini-1.5-pro")
        temperature: Sampling temperature
        json_mode: Whether to request JSON output format (OpenAI only, default True)
        **kwargs: Additional model-specific arguments

    Returns:
        LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)
    """

    # Detect provider based on model name
    if model.startswith("gemini"):
        return _create_gemini_llm(model, temperature, **kwargs)
    else:
        return _create_openai_llm(model, temperature, json_mode=json_mode, **kwargs)


def _create_openai_llm(model: str, temperature: float, json_mode: bool = True, **kwargs):
    """Create OpenAI LLM instance"""
    from langchain_openai import ChatOpenAI

    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        model_kwargs=model_kwargs,
        **kwargs
    )


def _create_gemini_llm(model: str, temperature: float, **kwargs):
    """Create Google Gemini LLM instance"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "langchain-google-genai is required for Gemini models. "
            "Install with: pip install langchain-google-genai"
        )

    google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required for Gemini models"
        )

    # Note: Gemini doesn't natively support system messages
    # The library handles this automatically in newer versions
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=google_api_key,
        **kwargs
    )


def get_model_provider(model: str) -> str:
    """
    Get the provider name for a given model.

    Args:
        model: Model identifier

    Returns:
        Provider name ("openai" or "google")
    """
    if model.startswith("gemini"):
        return "google"
    else:
        return "openai"


def is_gemini_model(model: str) -> bool:
    """Check if a model is a Gemini model"""
    return model.startswith("gemini")


def is_openai_model(model: str) -> bool:
    """Check if a model is an OpenAI model"""
    return not model.startswith("gemini")


def get_model_name(llm) -> str:
    """
    Get the model name from an LLM instance, handling different providers.

    Args:
        llm: LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)

    Returns:
        Model name string
    """
    # Try different attribute names used by different providers
    if hasattr(llm, 'model_name'):
        return llm.model_name
    elif hasattr(llm, 'model'):
        return llm.model
    else:
        # Fallback: return class name if no model attribute found
        return llm.__class__.__name__


def extract_token_usage(response) -> dict:
    """
    Extract token usage from LLM response, handling different providers.

    Args:
        response: LLM response object

    Returns:
        Dictionary with prompt_tokens, completion_tokens, and total_tokens
    """
    metadata = getattr(response, 'response_metadata', {})

    # OpenAI format: response_metadata.token_usage
    if 'token_usage' in metadata:
        token_usage = metadata['token_usage']
        return {
            "prompt_tokens": token_usage.get("prompt_tokens", 0),
            "completion_tokens": token_usage.get("completion_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0)
        }

    # Gemini format: response_metadata.usage_metadata
    if 'usage_metadata' in metadata:
        usage = metadata['usage_metadata']
        prompt_tokens = usage.get('prompt_token_count', 0)
        completion_tokens = usage.get('candidates_token_count', 0)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }

    # Fallback: return zeros if no token info found
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
