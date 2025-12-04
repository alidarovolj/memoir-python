"""Custom exceptions for the application"""


class MemoirException(Exception):
    """Base exception for Memoir application"""
    pass


class AuthenticationError(MemoirException):
    """Authentication failed"""
    pass


class AuthorizationError(MemoirException):
    """Authorization failed"""
    pass


class NotFoundError(MemoirException):
    """Resource not found"""
    pass


class ValidationError(MemoirException):
    """Validation error"""
    pass


class AIServiceError(MemoirException):
    """AI service error"""
    pass


class DatabaseError(MemoirException):
    """Database operation error"""
    pass

