"""SDK exceptions"""


class AuroraLifeError(Exception):
    """Base exception for AURORA_LIFE SDK."""
    pass


class AuthenticationError(AuroraLifeError):
    """Authentication failed."""
    pass


class ValidationError(AuroraLifeError):
    """Request validation failed."""
    pass


class NotFoundError(AuroraLifeError):
    """Resource not found."""
    pass


class RateLimitError(AuroraLifeError):
    """Rate limit exceeded."""
    pass
