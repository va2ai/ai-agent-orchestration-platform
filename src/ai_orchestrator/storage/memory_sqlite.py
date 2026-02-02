"""
SQLite implementation of MemoryStore.

Local-first sqlite memory store with no external dependencies.
Data persists across process restarts.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from ai_orchestrator.plugins import MemoryItem, MemoryStore, MemoryStoreError
from ai_orchestrator.plugins.types import JsonValue


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _stringify(value: Mapping[str, JsonValue]) -> str:
    """Create a searchable text representation of a value."""
    parts: list[str] = []
    for k, v in value.items():
        parts.append(str(k))
        parts.append(str(v))
    return " ".join(parts).lower()


@dataclass
class SQLiteMemoryStore:
    """Local-first sqlite memory store (no external deps).

    Storage schema:
        namespace TEXT
        key TEXT
        value_json TEXT
        search_text TEXT
        created_at TEXT
        updated_at TEXT
        ttl_seconds INTEGER NULL

    Search is a naive LIKE scan over search_text.
    For production-grade recall, you can replace this with:
        - SQLite FTS5 (if available)
        - a vector store
        - memU (later)

    Example:
        store = SQLiteMemoryStore(path="./memory.db")
        store.put(namespace="agent1", key="fact_1", value={"content": "User prefers dark mode"})
        item = store.get(namespace="agent1", key="fact_1")
        results = store.search(namespace="agent1", query="dark mode", k=5)
    """

    path: str = ".ai_orchestrator_memory.sqlite3"

    def __post_init__(self) -> None:
        """Initialize the database schema."""
        try:
            db_path = Path(self.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._conn() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_items (
                        namespace TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value_json TEXT NOT NULL,
                        search_text TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        ttl_seconds INTEGER NULL,
                        PRIMARY KEY(namespace, key)
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_updated "
                    "ON memory_items(namespace, updated_at);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_search "
                    "ON memory_items(namespace, search_text);"
                )
                conn.commit()
        except Exception as e:
            raise MemoryStoreError(
                "Failed to initialize SQLiteMemoryStore",
                backend=self.backend_name,
                cause=e,
            )

    @property
    def backend_name(self) -> str:
        return "sqlite"

    def _conn(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

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
            now = _now_iso()
            value_json = json.dumps(value, ensure_ascii=False)
            search_text = _stringify(value)

            with self._conn() as conn:
                row = conn.execute(
                    "SELECT created_at, value_json FROM memory_items "
                    "WHERE namespace = ? AND key = ?",
                    (namespace, key),
                ).fetchone()

                if row is None:
                    conn.execute(
                        """
                        INSERT INTO memory_items
                        (namespace, key, value_json, search_text, created_at, updated_at, ttl_seconds)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (namespace, key, value_json, search_text, now, now, ttl_seconds),
                    )
                else:
                    # Merge values (shallow) to preserve stable keys unless overwritten
                    existing = json.loads(row["value_json"])
                    if isinstance(existing, dict):
                        merged = dict(existing)
                        merged.update(value)
                    else:
                        merged = dict(value)

                    conn.execute(
                        """
                        UPDATE memory_items
                        SET value_json = ?, search_text = ?, updated_at = ?, ttl_seconds = ?
                        WHERE namespace = ? AND key = ?
                        """,
                        (
                            json.dumps(merged, ensure_ascii=False),
                            _stringify(merged),
                            now,
                            ttl_seconds,
                            namespace,
                            key,
                        ),
                    )
                conn.commit()
        except Exception as e:
            raise MemoryStoreError(
                "Failed to put memory item",
                backend=self.backend_name,
                cause=e,
            )

    def get(self, *, namespace: str, key: str) -> Optional[MemoryItem]:
        """Get a memory item by key."""
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM memory_items WHERE namespace = ? AND key = ?",
                    (namespace, key),
                ).fetchone()

            if row is None:
                return None

            return MemoryItem(
                key=row["key"],
                value=json.loads(row["value_json"]),
                created_at_iso=row["created_at"],
                updated_at_iso=row["updated_at"],
                score=None,
                metadata={"ttl_seconds": row["ttl_seconds"]},
            )
        except Exception as e:
            raise MemoryStoreError(
                "Failed to get memory item",
                backend=self.backend_name,
                cause=e,
            )

    def delete(self, *, namespace: str, key: str) -> None:
        """Delete a memory item."""
        try:
            with self._conn() as conn:
                conn.execute(
                    "DELETE FROM memory_items WHERE namespace = ? AND key = ?",
                    (namespace, key),
                )
                conn.commit()
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
        """Return top-k relevant memory items using LIKE-based search."""
        try:
            q = (query or "").lower().strip()

            with self._conn() as conn:
                if not q:
                    rows = conn.execute(
                        """
                        SELECT * FROM memory_items
                        WHERE namespace = ?
                        ORDER BY updated_at DESC
                        LIMIT ?
                        """,
                        (namespace, k),
                    ).fetchall()
                else:
                    # Naive LIKE scan. Good enough for local-first MVP.
                    like = f"%{q}%"
                    rows = conn.execute(
                        """
                        SELECT * FROM memory_items
                        WHERE namespace = ?
                          AND search_text LIKE ?
                        ORDER BY updated_at DESC
                        LIMIT ?
                        """,
                        (namespace, like, k),
                    ).fetchall()

            out: list[MemoryItem] = []
            for row in rows:
                out.append(
                    MemoryItem(
                        key=row["key"],
                        value=json.loads(row["value_json"]),
                        created_at_iso=row["created_at"],
                        updated_at_iso=row["updated_at"],
                        score=None,
                        metadata={"ttl_seconds": row["ttl_seconds"]},
                    )
                )
            return out
        except Exception as e:
            raise MemoryStoreError(
                "Failed to search memory",
                backend=self.backend_name,
                cause=e,
            )

    def compact(self, *, namespace: str) -> Mapping[str, Any]:
        """Return statistics about the namespace."""
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM memory_items WHERE namespace = ?",
                    (namespace,),
                ).fetchone()

            return {
                "namespace": namespace,
                "count": int(row["cnt"]),
                "backend": self.backend_name,
            }
        except Exception as e:
            raise MemoryStoreError(
                "Failed to compact memory",
                backend=self.backend_name,
                cause=e,
            )

    def clear(self, *, namespace: Optional[str] = None) -> None:
        """Clear all data in a namespace or all namespaces.

        Args:
            namespace: If provided, clear only this namespace.
                       If None, clear all data.
        """
        try:
            with self._conn() as conn:
                if namespace is None:
                    conn.execute("DELETE FROM memory_items")
                else:
                    conn.execute(
                        "DELETE FROM memory_items WHERE namespace = ?",
                        (namespace,),
                    )
                conn.commit()
        except Exception as e:
            raise MemoryStoreError(
                "Failed to clear memory",
                backend=self.backend_name,
                cause=e,
            )

    def list_namespaces(self) -> Sequence[str]:
        """List all namespaces."""
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT namespace FROM memory_items ORDER BY namespace"
                ).fetchall()
            return [row["namespace"] for row in rows]
        except Exception as e:
            raise MemoryStoreError(
                "Failed to list namespaces",
                backend=self.backend_name,
                cause=e,
            )
