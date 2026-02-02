"""
Storage implementations for ai_orchestrator.

This package provides:
- PRDStorage: JSON file-based storage for PRD documents and sessions
- InMemoryStore: Dependency-free memory store (great for tests)
- SQLiteMemoryStore: Local-first persistent memory store

Example:
    from ai_orchestrator.storage import InMemoryStore, SQLiteMemoryStore

    # For tests and demos
    memory = InMemoryStore()

    # For persistent local storage
    memory = SQLiteMemoryStore(path="./data/memory.db")

    # Store and retrieve
    memory.put(namespace="agent1", key="fact_1", value={"content": "User prefers dark mode"})
    item = memory.get(namespace="agent1", key="fact_1")
    results = memory.search(namespace="agent1", query="dark mode", k=5)
"""

from .memory_inmemory import InMemoryStore
from .memory_sqlite import SQLiteMemoryStore

__all__ = [
    "InMemoryStore",
    "SQLiteMemoryStore",
]
