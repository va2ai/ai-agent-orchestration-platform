"""
Retriever protocol for document retrieval backends.

This interface abstracts over vector stores (pgvector, Pinecone, Chroma, FAISS)
and future reasoning-based retrieval (PageIndex).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .types import DocumentChunk, RetrievedChunk


class RetrieverError(RuntimeError):
    """Raised when retrieval fails."""

    def __init__(
        self,
        message: str,
        *,
        backend: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.backend = backend
        self.__cause__ = cause


@runtime_checkable
class Retriever(Protocol):
    """Abstract retrieval backend.

    You can implement this with:
    - pgvector / Pinecone / Chroma / FAISS / etc. (vector-based)
    - a hybrid search layer (BM25 + vectors)
    - PageIndex (vectorless, reasoning-based) - future integration

    The interface is intentionally generic:
    - input: query string + optional filters
    - output: RetrievedChunk list with scores
    """

    @property
    def backend_name(self) -> str:
        """Short name like 'pgvector', 'chroma', 'faiss', 'pageindex'."""
        ...

    def index(
        self,
        chunks: Sequence[DocumentChunk],
        *,
        namespace: str,
    ) -> None:
        """Upsert/index chunks into the backend.

        Args:
            chunks: Document chunks to index.
            namespace: Logical namespace for isolation (e.g., per-user, per-session).

        Raises:
            RetrieverError: On indexing failures.
        """
        ...

    def search(
        self,
        query: str,
        *,
        namespace: str,
        k: int = 10,
        filters: Optional[Mapping[str, Any]] = None,
    ) -> Sequence[RetrievedChunk]:
        """Search and return top-k relevant chunks.

        Args:
            query: Search query string.
            namespace: Namespace to search within.
            k: Number of results to return.
            filters: Optional metadata filters (e.g., {"source": "medical"}).

        Returns:
            List of RetrievedChunk objects sorted by relevance score (descending).

        Raises:
            RetrieverError: On search failures.
        """
        ...

    def delete(
        self,
        *,
        namespace: str,
        chunk_ids: Optional[Sequence[str]] = None,
    ) -> None:
        """Delete chunks from the index.

        Args:
            namespace: Namespace to delete from.
            chunk_ids: Specific chunk IDs to delete. If None, deletes entire namespace.

        Raises:
            RetrieverError: On deletion failures.
        """
        ...
