"""
Base domain exceptions for Personal Analytics System.
Following Onion Architecture: Core domain exceptions are independent of web or database frameworks.
"""

class DomainException(Exception):
    """Base exception for all domain-level errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EntityNotFoundException(DomainException):
    """Raised when a domain entity is not found."""
    def __init__(self, entity_name: str, identifier: str):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.")

class ValidationErrorException(DomainException):
    """Raised when domain validation fails."""
    def __init__(self, message: str, errors: list = None):
        self.errors = errors or []
        super().__init__(message)

class DuplicateEntityException(DomainException):
    """Raised when an entity already exists."""
    def __init__(self, entity_name: str, identifier: str):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} with identifier '{identifier}' already exists.")
