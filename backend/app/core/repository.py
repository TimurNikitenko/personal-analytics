"""
Generic Repository Protocols for Onion Architecture.
Enforces Dependency Inversion Principle (DIP): Domain services depend on repository protocols,
not concrete ORM / database drivers.
"""

from typing import Protocol, TypeVar, Generic, List, Optional, Any

T = TypeVar("T")
ID = TypeVar("ID")

class BaseRepository(Protocol, Generic[T, ID]):
    """Generic base repository protocol."""
    
    def get_by_id(self, id_val: ID) -> Optional[T]:
        ...
        
    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        ...
        
    def add(self, entity: T) -> T:
        ...
        
    def delete(self, id_val: ID) -> bool:
        ...
