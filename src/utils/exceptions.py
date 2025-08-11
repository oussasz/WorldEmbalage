class AppError(Exception):
    """Base application exception."""


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


class PermissionError(AppError):  # pragma: no cover
    pass

__all__ = ['AppError', 'NotFoundError', 'ValidationError', 'PermissionError']
