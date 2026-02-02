"""
Plugin interfaces for ai_orchestrator.

Goal: keep orchestration logic pure and vendor-agnostic.

Interfaces:
- ModelProvider: LLM generation (OpenAI/Gemini/Claude) behind an interface
- EmbeddingProvider: Text embedding generation
- Retriever: Retrieval backends (vector now; PageIndex later)
- MemoryStore: Memory backends (local-first now; memU later)

These are *interfaces* + lightweight, dependency-free reference types.
Implementations live in separate modules (e.g., storage/memory_inmemory.py).

Example usage:
    from ai_orchestrator.plugins import ModelProvider, ChatMessage, ModelResponse

    class MyProvider:
        @property
        def provider_name(self) -> str:
            return "my_provider"

        def generate(self, messages, **kwargs) -> ModelResponse:
            # Your implementation here
            return ModelResponse(text="Hello!")

    # Type checking works:
    provider: ModelProvider = MyProvider()
"""

from .types import (
    ChatMessage,
    ModelResponse,
    ModelUsage,
    DocumentChunk,
    RetrievedChunk,
    MemoryItem,
    JsonValue,
    JsonPrimitive,
    Role,
)

from .model_provider import ModelProvider, EmbeddingProvider, ProviderError
from .retriever import Retriever, RetrieverError
from .memory_store import MemoryStore, MemoryStoreError

__all__ = [
    # Types
    "ChatMessage",
    "ModelResponse",
    "ModelUsage",
    "DocumentChunk",
    "RetrievedChunk",
    "MemoryItem",
    "JsonValue",
    "JsonPrimitive",
    "Role",
    # Model Provider
    "ModelProvider",
    "EmbeddingProvider",
    "ProviderError",
    # Retriever
    "Retriever",
    "RetrieverError",
    # Memory Store
    "MemoryStore",
    "MemoryStoreError",
]
