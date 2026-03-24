"""
Custom exceptions for the application.
"""

from fastapi import HTTPException, status


class CustomException(Exception):
    """Base exception for the application."""
    pass


class TenantNotFound(CustomException):
    """Raised when a tenant is not found."""
    pass


class UserNotFound(CustomException):
    """Raised when a user is not found."""
    pass


class DocumentNotFound(CustomException):
    """Raised when a document is not found."""
    pass


class UnauthorizedException(CustomException):
    """Raised when user is not authorized."""
    pass


class InvalidTenantAccess(CustomException):
    """Raised when user tries to access another tenant's data."""
    pass


class DocumentProcessingError(CustomException):
    """Raised when document processing fails."""
    pass


class AccountLockedError(CustomException):
    """Raised when an account is temporarily locked due to failed login attempts."""
    pass


class PasswordValidationError(CustomException):
    """Raised when a password does not meet complexity requirements."""
    pass
