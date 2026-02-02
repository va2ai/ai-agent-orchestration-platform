"""
In-memory implementation of MemoryStore.

Dependency-free memory store, great for tests and local demos.
Data is lost when the process exits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence

from ai_orchestrator.plugins import MemoryItem, MemoryStore, MemoryStoreError
from ai_orchestrator.plugins.types import JsonValue


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _stringify(value: Mapping[str, JsonValue]) -> str:
    """Create a searchable text representation of a value (dependency-free)."""
    parts: list[str] = []
    for k, v in value.items():
        parts.append(str(k))
        parts.append(str(v))
    return " ".join(parts).lower()


@dataclass
class InMemoryStore:
    """Dependency-free memory store.

    Great for tests and local demos. Data is stored in a nested dict structure.

    Example:
        store = InMemoryStore()
        store.put(namespace="agent1", key="fact_1", value={"content": "User prefers dark mode"})
        item = store.get(namespace="agent1", key="fact_1")
        results = store.search(namespace="agent1", query="dark mode", k=5)
    """

    _data: Dict[str, Dict[str, MemoryItem]] = field(default_factory=dict)

    @property
    def backend_name(self) -> str:
        return "inmemory"

    def put(
        self,
        *,
        namespace: str,
        key: str,
        value: Mapping[str, JsonValue],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Insert or update a memory item."""
        try:
            ns = self._data.setdefault(namespace, {})
            now = _now_iso()
            existing = ns.get(key)

            if existing is None:
                ns[key] = MemoryItem(
                    key=key,
                    value=dict(value),
                    created_at_iso=now,
                    updated_at_iso=now,
                    score=None,
                    metadata={"ttl_seconds": ttl_seconds, "_search_text": _stringify(value)},
                )
            else:
                # Merge values (shallow) to preserve stable keys unless overwritten
                new_value: MutableMapping[str, JsonValue] = dict(existing.value)
                new_value.update(value)
                ns[key] = MemoryItem(
                    key=key,
                    value=new_value,
                    created_at_iso=existing.created_at_iso,
                    updated_at_iso=now,
                    score=None,
                    metadata={"ttl_seconds": ttl_seconds, "_search_text": _stringify(new_value)},
                )
        except Exception as e:
            raise MemoryStoreError(
                "Failed to put memory item",
                backend=self.backend_name,
                cause=e,
            )

    def get(self, *, namespace: str, key: str) -> Optional[MemoryItem]:
        """Get a memory item by key."""
        return self._data.get(namespace, {}).get(key)

    def delete(self, *, namespace: str, key: str) -> None:
        """Delete a memory item."""
        try:
            ns = self._data.get(namespace)
            if not ns:
                return
            ns.pop(key, None)
        except Exception as e:
            raise MemoryStoreError(
                "Failed to delete memory item",
                backend=self.backend_name,
                cause=e,
            )

    def search(
        self,
        *,
        namespace: str,
        query: str,
        k: int = 10,
    ) -> Sequence[MemoryItem]:
        """Return top-k relevant memory items using naive term matching."""
        q = (query or "").lower().strip()
        ns = self._data.get(namespace, {})

        if not q:
            # Return newest items by updated_at
            items = sorted(ns.values(), key=lambda x: x.updated_at_iso, reverse=True)
            return items[:k]

        scored: list[tuple[float, MemoryItem]] = []
        for item in ns.values():
            hay = str(item.metadata.get("_search_text", ""))
            # Naive term-hit scoring (fast + dependency-free)
            score = 0.0
            for term in q.split():
                if term in hay:
                    score += 1.0
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda t: t[0], reverse=True)
        out: list[MemoryItem] = []
        for s, item in scored[:k]:
            out.append(
                MemoryItem(
                    key=item.key,
                    value=item.value,
                    created_at_iso=item.created_at_iso,
                    updated_at_iso=item.updated_at_iso,
                    score=s,
                    metadata=item.metadata,
                )
            )
        return out

    def compact(self, *, namespace: str) -> Mapping[str, Any]:
        """Return statistics about the namespace."""
        ns = self._data.get(namespace, {})
        return {
            "namespace": namespace,
            "count": len(ns),
            "backend": self.backend_name,
        }

    def clear(self, *, namespace: Optional[str] = None) -> None:
        """Clear all data in a namespace or all namespaces.

        Args:
            namespace: If provided, clear only this namespace.
                       If None, clear all data.
        """
        if namespace is None:
            self._data.clear()
        elif namespace in self._data:
            del self._data[namespace]

    def list_namespaces(self) -> Sequence[str]:
        """List all namespaces."""
        return list(self._data.keys())
