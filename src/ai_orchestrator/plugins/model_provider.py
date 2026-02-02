"""
ModelProvider protocol for LLM generation.

This interface abstracts over OpenAI/Gemini/Claude/local providers.
The orchestration logic stays pure and vendor-agnostic.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .types import ChatMessage, ModelResponse


class ProviderError(RuntimeError):
    """Raised when a model provider fails (network, auth, rate limit, etc.)."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.__cause__ = cause


@runtime_checkable
class ModelProvider(Protocol):
    """Text generation provider.

    Design constraints:
    - Pure interface (no OpenAI/Gemini/Claude imports here).
    - Supports chat-style messages.
    - Returns a ModelResponse that can carry raw provider payloads in `raw`.

    Example implementations:
    - OpenAIModelProvider (wraps openai.ChatCompletion)
    - GeminiModelProvider (wraps google.generativeai)
    - ClaudeModelProvider (wraps anthropic.Anthropic)
    - LocalModelProvider (wraps ollama, llamacpp, etc.)
    """

    @property
    def provider_name(self) -> str:
        """Short name like 'openai', 'gemini', 'claude', 'local'."""
        ...

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ModelResponse:
        """Generate text from messages.

        Args:
            messages: Chat messages in conversation order.
            model: Model identifier (e.g., 'gpt-4o', 'gemini-2.5-flash').
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens to generate.
            top_p: Nucleus sampling threshold.
            stop: Stop sequences.
            metadata: Provider-specific options.

        Returns:
            ModelResponse with generated text and usage info.

        Raises:
            ProviderError: On network, auth, or rate limit failures.
        """
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Optional embedding provider (some ModelProviders may also implement this)."""

    @property
    def provider_name(self) -> str:
        """Short name like 'openai', 'gemini', 'claude', 'local'."""
        ...

    def embed(
        self,
        texts: Sequence[str],
        *,
        model: Optional[str] = None,
    ) -> Sequence[Sequence[float]]:
        """Return embeddings aligned to `texts` order.

        Args:
            texts: List of texts to embed.
            model: Embedding model identifier.

        Returns:
            List of embedding vectors, one per input text.

        Raises:
            ProviderError: On network, auth, or rate limit failures.
        """
        ...
