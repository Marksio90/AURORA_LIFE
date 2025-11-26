"""
JWT Token handling - generation, validation, refresh
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings


# Token configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data to encode (usually {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token (longer expiration).

    Args:
        data: Payload data to encode

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode access token and return subject (user_id).

    Args:
        token: JWT access token

    Returns:
        User ID from token subject, or None if invalid
    """
    payload = verify_token(token)

    if payload is None:
        return None

    # Verify it's an access token
    if payload.get("type") != "access":
        return None

    user_id: str = payload.get("sub")
    return user_id


def decode_refresh_token(token: str) -> Optional[str]:
    """
    Decode refresh token and return subject (user_id).

    Args:
        token: JWT refresh token

    Returns:
        User ID from token subject, or None if invalid
    """
    payload = verify_token(token)

    if payload is None:
        return None

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        return None

    user_id: str = payload.get("sub")
    return user_id
