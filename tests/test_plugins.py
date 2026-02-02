"""
Tests for plugin interfaces and implementations.

Tests the core plugin protocols and local-first memory stores.
"""
import pytest
from typing import Any, Dict, Mapping, Optional, Sequence

from ai_orchestrator.plugins import (
    ChatMessage,
    ModelResponse,
    ModelUsage,
    DocumentChunk,
    RetrievedChunk,
    MemoryItem,
    ModelProvider,
    EmbeddingProvider,
    Retriever,
    MemoryStore,
    ProviderError,
    RetrieverError,
    MemoryStoreError,
)


class TestPluginTypes:
    """Tests for plugin type dataclasses."""

    def test_chat_message(self):
        """Test ChatMessage creation and immutability."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.metadata == {}

        # With metadata
        msg2 = ChatMessage(
            role="assistant",
            content="Hi there",
            name="helper",
            metadata={"key": "value"},
        )
        assert msg2.name == "helper"
        assert msg2.metadata["key"] == "value"

    def test_model_usage(self):
        """Test ModelUsage creation."""
        usage = ModelUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.001,
            output_cost_usd=0.002,
        )
        assert usage.prompt_tokens == 100
        assert usage.total_tokens == 150

    def test_model_response(self):
        """Test ModelResponse creation."""
        usage = ModelUsage(total_tokens=100)
        response = ModelResponse(
            text="Generated text",
            model="gpt-4o",
            usage=usage,
            metadata={"finish_reason": "stop"},
        )
        assert response.text == "Generated text"
        assert response.model == "gpt-4o"
        assert response.usage.total_tokens == 100

    def test_document_chunk(self):
        """Test DocumentChunk creation."""
        chunk = DocumentChunk(
            chunk_id="chunk_001",
            text="This is a chunk of text.",
            metadata={"source": "document.pdf", "page": 1},
        )
        assert chunk.chunk_id == "chunk_001"
        assert chunk.text == "This is a chunk of text."
        assert chunk.metadata["page"] == 1

    def test_retrieved_chunk(self):
        """Test RetrievedChunk creation."""
        chunk = DocumentChunk(chunk_id="1", text="text")
        retrieved = RetrievedChunk(
            chunk=chunk,
            score=0.95,
            metadata={"method": "vector"},
        )
        assert retrieved.chunk.chunk_id == "1"
        assert retrieved.score == 0.95

    def test_memory_item(self):
        """Test MemoryItem creation."""
        item = MemoryItem(
            key="fact_001",
            value={"content": "User prefers dark mode"},
            created_at_iso="2026-01-01T00:00:00Z",
            updated_at_iso="2026-01-02T00:00:00Z",
            score=0.8,
        )
        assert item.key == "fact_001"
        assert item.value["content"] == "User prefers dark mode"


class TestProtocolCompliance:
    """Test that fake implementations satisfy protocols."""

    def test_model_provider_protocol(self):
        """Test that a class can satisfy ModelProvider protocol."""

        class FakeModelProvider:
            @property
            def provider_name(self) -> str:
                return "fake"

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
                return ModelResponse(text="fake response")

        provider = FakeModelProvider()
        assert isinstance(provider, ModelProvider)
        assert provider.provider_name == "fake"

        response = provider.generate([ChatMessage(role="user", content="Hello")])
        assert response.text == "fake response"

    def test_embedding_provider_protocol(self):
        """Test that a class can satisfy EmbeddingProvider protocol."""

        class FakeEmbeddingProvider:
            @property
            def provider_name(self) -> str:
                return "fake"

            def embed(
                self,
                texts: Sequence[str],
                *,
                model: Optional[str] = None,
            ) -> Sequence[Sequence[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]

        provider = FakeEmbeddingProvider()
        assert isinstance(provider, EmbeddingProvider)

        embeddings = provider.embed(["hello", "world"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3

    def test_retriever_protocol(self):
        """Test that a class can satisfy Retriever protocol."""

        class FakeRetriever:
            @property
            def backend_name(self) -> str:
                return "fake"

            def index(
                self,
                chunks: Sequence[DocumentChunk],
                *,
                namespace: str,
            ) -> None:
                pass

            def search(
                self,
                query: str,
                *,
                namespace: str,
                k: int = 10,
                filters: Optional[Mapping[str, Any]] = None,
            ) -> Sequence[RetrievedChunk]:
                return []

            def delete(
                self,
                *,
                namespace: str,
                chunk_ids: Optional[Sequence[str]] = None,
            ) -> None:
                pass

        retriever = FakeRetriever()
        assert isinstance(retriever, Retriever)
        assert retriever.backend_name == "fake"

    def test_memory_store_protocol(self):
        """Test that a class can satisfy MemoryStore protocol."""

        class FakeMemoryStore:
            @property
            def backend_name(self) -> str:
                return "fake"

            def put(
                self,
                *,
                namespace: str,
                key: str,
                value: Mapping[str, Any],
                ttl_seconds: Optional[int] = None,
            ) -> None:
                pass

            def get(self, *, namespace: str, key: str) -> Optional[MemoryItem]:
                return None

            def delete(self, *, namespace: str, key: str) -> None:
                pass

            def search(
                self,
                *,
                namespace: str,
                query: str,
                k: int = 10,
            ) -> Sequence[MemoryItem]:
                return []

            def compact(self, *, namespace: str) -> Mapping[str, Any]:
                return {}

        store = FakeMemoryStore()
        assert isinstance(store, MemoryStore)


class TestErrors:
    """Test custom error classes."""

    def test_provider_error(self):
        """Test ProviderError creation."""
        error = ProviderError("API failed", provider="openai")
        assert str(error) == "API failed"
        assert error.provider == "openai"

        # With cause
        cause = ValueError("bad input")
        error2 = ProviderError("Wrapped error", cause=cause)
        assert error2.__cause__ is cause

    def test_retriever_error(self):
        """Test RetrieverError creation."""
        error = RetrieverError("Search failed", backend="chroma")
        assert str(error) == "Search failed"
        assert error.backend == "chroma"

    def test_memory_store_error(self):
        """Test MemoryStoreError creation."""
        error = MemoryStoreError("Write failed", backend="sqlite")
        assert str(error) == "Write failed"
        assert error.backend == "sqlite"
