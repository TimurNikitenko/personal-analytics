"""
Pytest configuration and global test fixtures for Onion Architecture unit and integration testing.
"""

import pytest
from typing import Dict, Any, List, Optional, TypeVar, Generic
from backend.app.core.repository import BaseRepository

T = TypeVar("T")
ID = TypeVar("ID")

class MemoryRepository(Generic[T, ID]):
    """Generic in-memory mock repository for fast, isolated unit testing of domain services."""

    def __init__(self, id_field: str = "id"):
        self._storage: Dict[Any, T] = {}
        self._id_field = id_field

    def get_by_id(self, id_val: ID) -> Optional[T]:
        return self._storage.get(id_val)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        items = list(self._storage.values())
        return items[offset : offset + limit]

    def add(self, entity: T) -> T:
        id_val = getattr(entity, self._id_field, None) or len(self._storage) + 1
        setattr(entity, self._id_field, id_val)
        self._storage[id_val] = entity
        return entity

    def delete(self, id_val: ID) -> bool:
        if id_val in self._storage:
            del self._storage[id_val]
            return True
        return False

    def clear(self):
        self._storage.clear()

@pytest.fixture
def memory_repo_factory():
    """Fixture factory for creating in-memory mock repositories."""
    def _create(id_field: str = "id"):
        return MemoryRepository(id_field=id_field)
    return _create
