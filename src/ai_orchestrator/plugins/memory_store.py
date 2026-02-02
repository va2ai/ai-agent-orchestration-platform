"""
MemoryStore protocol for long-term agent memory.

This interface abstracts over local storage (in-memory, SQLite) and
future agentic memory frameworks (memU).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .types import MemoryItem, JsonValue


class MemoryStoreError(RuntimeError):
    """Raised when memory operations fail."""

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
class MemoryStore(Protocol):
    """Abstract long-term memory store (local first; memU later).

    Key design points:
    - Namespace per agent/workflow/user/case/etc.
    - Store JSON-ish payloads for portability.
    - Provide a lightweight search API for recall.
    - Support TTL for automatic expiration.

    Example implementations:
    - InMemoryStore (dependency-free, great for tests)
    - SQLiteMemoryStore (local persistence, no external deps)
    - MemUStore (agentic memory framework) - future integration
    """

    @property
    def backend_name(self) -> str:
        """Short name like 'inmemory', 'sqlite', 'memu'."""
        ...

    def put(
        self,
        *,
        namespace: str,
        key: str,
        value: Mapping[str, JsonValue],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Insert or update a memory item.

        If the key exists, the value is merged (shallow update).

        Args:
            namespace: Logical namespace for isolation.
            key: Unique key within the namespace.
            value: JSON-serializable payload.
            ttl_seconds: Optional time-to-live in seconds.

        Raises:
            MemoryStoreError: On storage failures.
        """
        ...

    def get(
        self,
        *,
        namespace: str,
        key: str,
    ) -> Optional[MemoryItem]:
        """Get a memory item by key.

        Args:
            namespace: Namespace to search in.
            key: Key to retrieve.

        Returns:
            MemoryItem if found, None otherwise.
        """
        ...

    def delete(
        self,
        *,
        namespace: str,
        key: str,
    ) -> None:
        """Delete a memory item.

        Args:
            namespace: Namespace containing the item.
            key: Key to delete.

        Raises:
            MemoryStoreError: On deletion failures.
        """
        ...

    def search(
        self,
        *,
        namespace: str,
        query: str,
        k: int = 10,
    ) -> Sequence[MemoryItem]:
        """Return top-k relevant memory items.

        Args:
            namespace: Namespace to search in.
            query: Search query string.
            k: Number of results to return.

        Returns:
            List of MemoryItem objects with optional scores.
        """
        ...

    def compact(
        self,
        *,
        namespace: str,
    ) -> Mapping[str, Any]:
        """Optional maintenance operation (summarize, merge, prune).

        Args:
            namespace: Namespace to compact.

        Returns:
            Statistics about the compaction operation.
        """
        ...
