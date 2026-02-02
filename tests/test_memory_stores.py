"""
Tests for memory store implementations.

Tests InMemoryStore and SQLiteMemoryStore.
"""
import os
import tempfile
import pytest

from ai_orchestrator.storage import InMemoryStore, SQLiteMemoryStore
from ai_orchestrator.plugins import MemoryStore


class TestInMemoryStore:
    """Tests for InMemoryStore."""

    def test_protocol_compliance(self):
        """Test that InMemoryStore satisfies MemoryStore protocol."""
        store = InMemoryStore()
        assert isinstance(store, MemoryStore)
        assert store.backend_name == "inmemory"

    def test_put_and_get(self):
        """Test basic put and get operations."""
        store = InMemoryStore()

        store.put(
            namespace="test",
            key="fact_1",
            value={"content": "User prefers dark mode"},
        )

        item = store.get(namespace="test", key="fact_1")
        assert item is not None
        assert item.key == "fact_1"
        assert item.value["content"] == "User prefers dark mode"

    def test_get_nonexistent(self):
        """Test get for nonexistent key returns None."""
        store = InMemoryStore()
        item = store.get(namespace="test", key="nonexistent")
        assert item is None

    def test_put_updates_existing(self):
        """Test that put merges with existing values."""
        store = InMemoryStore()

        store.put(namespace="test", key="user_1", value={"name": "Alice"})
        store.put(namespace="test", key="user_1", value={"preference": "dark"})

        item = store.get(namespace="test", key="user_1")
        assert item is not None
        assert item.value["name"] == "Alice"
        assert item.value["preference"] == "dark"

    def test_delete(self):
        """Test delete operation."""
        store = InMemoryStore()

        store.put(namespace="test", key="temp", value={"data": "temporary"})
        store.delete(namespace="test", key="temp")

        item = store.get(namespace="test", key="temp")
        assert item is None

    def test_delete_nonexistent(self):
        """Test delete on nonexistent key doesn't raise."""
        store = InMemoryStore()
        store.delete(namespace="test", key="nonexistent")  # Should not raise

    def test_search_with_query(self):
        """Test search with query string."""
        store = InMemoryStore()

        store.put(namespace="test", key="fact_1", value={"content": "User prefers dark mode"})
        store.put(namespace="test", key="fact_2", value={"content": "User likes coffee"})
        store.put(namespace="test", key="fact_3", value={"content": "User prefers light theme"})

        results = store.search(namespace="test", query="dark", k=10)
        assert len(results) >= 1
        # dark mode should be found
        assert any("dark" in str(r.value) for r in results)

    def test_search_empty_query(self):
        """Test search with empty query returns recent items."""
        store = InMemoryStore()

        store.put(namespace="test", key="item_1", value={"data": "first"})
        store.put(namespace="test", key="item_2", value={"data": "second"})

        results = store.search(namespace="test", query="", k=10)
        assert len(results) == 2

    def test_search_respects_k(self):
        """Test search respects k limit."""
        store = InMemoryStore()

        for i in range(10):
            store.put(namespace="test", key=f"item_{i}", value={"index": i})

        results = store.search(namespace="test", query="", k=3)
        assert len(results) == 3

    def test_compact(self):
        """Test compact returns statistics."""
        store = InMemoryStore()

        store.put(namespace="test", key="item_1", value={"data": "one"})
        store.put(namespace="test", key="item_2", value={"data": "two"})

        stats = store.compact(namespace="test")
        assert stats["namespace"] == "test"
        assert stats["count"] == 2
        assert stats["backend"] == "inmemory"

    def test_namespace_isolation(self):
        """Test that namespaces are isolated."""
        store = InMemoryStore()

        store.put(namespace="ns1", key="key", value={"data": "namespace 1"})
        store.put(namespace="ns2", key="key", value={"data": "namespace 2"})

        item1 = store.get(namespace="ns1", key="key")
        item2 = store.get(namespace="ns2", key="key")

        assert item1.value["data"] == "namespace 1"
        assert item2.value["data"] == "namespace 2"

    def test_clear_namespace(self):
        """Test clearing a single namespace."""
        store = InMemoryStore()

        store.put(namespace="ns1", key="key", value={"data": "1"})
        store.put(namespace="ns2", key="key", value={"data": "2"})

        store.clear(namespace="ns1")

        assert store.get(namespace="ns1", key="key") is None
        assert store.get(namespace="ns2", key="key") is not None

    def test_clear_all(self):
        """Test clearing all namespaces."""
        store = InMemoryStore()

        store.put(namespace="ns1", key="key", value={"data": "1"})
        store.put(namespace="ns2", key="key", value={"data": "2"})

        store.clear()

        assert store.get(namespace="ns1", key="key") is None
        assert store.get(namespace="ns2", key="key") is None

    def test_list_namespaces(self):
        """Test listing namespaces."""
        store = InMemoryStore()

        store.put(namespace="alpha", key="key", value={"data": "1"})
        store.put(namespace="beta", key="key", value={"data": "2"})

        namespaces = store.list_namespaces()
        assert "alpha" in namespaces
        assert "beta" in namespaces


class TestSQLiteMemoryStore:
    """Tests for SQLiteMemoryStore."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_protocol_compliance(self, temp_db):
        """Test that SQLiteMemoryStore satisfies MemoryStore protocol."""
        store = SQLiteMemoryStore(path=temp_db)
        assert isinstance(store, MemoryStore)
        assert store.backend_name == "sqlite"

    def test_put_and_get(self, temp_db):
        """Test basic put and get operations."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(
            namespace="test",
            key="fact_1",
            value={"content": "User prefers dark mode"},
        )

        item = store.get(namespace="test", key="fact_1")
        assert item is not None
        assert item.key == "fact_1"
        assert item.value["content"] == "User prefers dark mode"

    def test_get_nonexistent(self, temp_db):
        """Test get for nonexistent key returns None."""
        store = SQLiteMemoryStore(path=temp_db)
        item = store.get(namespace="test", key="nonexistent")
        assert item is None

    def test_put_updates_existing(self, temp_db):
        """Test that put merges with existing values."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="test", key="user_1", value={"name": "Alice"})
        store.put(namespace="test", key="user_1", value={"preference": "dark"})

        item = store.get(namespace="test", key="user_1")
        assert item is not None
        assert item.value["name"] == "Alice"
        assert item.value["preference"] == "dark"

    def test_delete(self, temp_db):
        """Test delete operation."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="test", key="temp", value={"data": "temporary"})
        store.delete(namespace="test", key="temp")

        item = store.get(namespace="test", key="temp")
        assert item is None

    def test_search_with_query(self, temp_db):
        """Test search with query string."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="test", key="fact_1", value={"content": "User prefers dark mode"})
        store.put(namespace="test", key="fact_2", value={"content": "User likes coffee"})
        store.put(namespace="test", key="fact_3", value={"content": "User prefers light theme"})

        results = store.search(namespace="test", query="dark", k=10)
        assert len(results) >= 1

    def test_search_empty_query(self, temp_db):
        """Test search with empty query returns recent items."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="test", key="item_1", value={"data": "first"})
        store.put(namespace="test", key="item_2", value={"data": "second"})

        results = store.search(namespace="test", query="", k=10)
        assert len(results) == 2

    def test_compact(self, temp_db):
        """Test compact returns statistics."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="test", key="item_1", value={"data": "one"})
        store.put(namespace="test", key="item_2", value={"data": "two"})

        stats = store.compact(namespace="test")
        assert stats["namespace"] == "test"
        assert stats["count"] == 2
        assert stats["backend"] == "sqlite"

    def test_namespace_isolation(self, temp_db):
        """Test that namespaces are isolated."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="ns1", key="key", value={"data": "namespace 1"})
        store.put(namespace="ns2", key="key", value={"data": "namespace 2"})

        item1 = store.get(namespace="ns1", key="key")
        item2 = store.get(namespace="ns2", key="key")

        assert item1.value["data"] == "namespace 1"
        assert item2.value["data"] == "namespace 2"

    def test_persistence(self, temp_db):
        """Test that data persists across store instances."""
        store1 = SQLiteMemoryStore(path=temp_db)
        store1.put(namespace="test", key="persistent", value={"data": "should persist"})

        # Create new store instance pointing to same file
        store2 = SQLiteMemoryStore(path=temp_db)
        item = store2.get(namespace="test", key="persistent")

        assert item is not None
        assert item.value["data"] == "should persist"

    def test_clear_namespace(self, temp_db):
        """Test clearing a single namespace."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="ns1", key="key", value={"data": "1"})
        store.put(namespace="ns2", key="key", value={"data": "2"})

        store.clear(namespace="ns1")

        assert store.get(namespace="ns1", key="key") is None
        assert store.get(namespace="ns2", key="key") is not None

    def test_clear_all(self, temp_db):
        """Test clearing all namespaces."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="ns1", key="key", value={"data": "1"})
        store.put(namespace="ns2", key="key", value={"data": "2"})

        store.clear()

        assert store.get(namespace="ns1", key="key") is None
        assert store.get(namespace="ns2", key="key") is None

    def test_list_namespaces(self, temp_db):
        """Test listing namespaces."""
        store = SQLiteMemoryStore(path=temp_db)

        store.put(namespace="alpha", key="key", value={"data": "1"})
        store.put(namespace="beta", key="key", value={"data": "2"})

        namespaces = store.list_namespaces()
        assert "alpha" in namespaces
        assert "beta" in namespaces
