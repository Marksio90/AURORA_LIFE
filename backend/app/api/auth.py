"""
Authentication API endpoints - login, logout, refresh, password reset
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.identity.service import IdentityService
from app.core.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.core.auth.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    PasswordChangeRequest
)
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login.

    Get access and refresh tokens for future requests using username/email and password.
    """
    identity_service = IdentityService(db)

    # Try to get user by email or username
    user = await identity_service.get_user_by_email(form_data.username)
    if not user:
        # Try username if email failed (form_data.username can be either)
        from sqlalchemy import select
        from app.models.user import User as UserModel
        result = await db.execute(
            select(UserModel).where(UserModel.username == form_data.username)
        )
        user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not identity_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds
    )


@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    JSON login endpoint (alternative to OAuth2 form).

    Accepts email or username with password.
    """
    identity_service = IdentityService(db)

    # Try email first, then username
    user = None
    if login_data.email:
        user = await identity_service.get_user_by_email(login_data.email)
    elif login_data.username:
        from sqlalchemy import select
        from app.models.user import User as UserModel
        result = await db.execute(
            select(UserModel).where(UserModel.username == login_data.username)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not identity_service.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    When access token expires, use refresh token to get a new access token
    without re-authenticating.
    """
    # Decode refresh token
    user_id_str = decode_refresh_token(refresh_data.refresh_token)

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists
    identity_service = IdentityService(db)
    user = await identity_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint.

    Since JWT tokens are stateless, logout is handled client-side by
    discarding tokens. This endpoint exists for logging/auditing purposes.

    In production, implement token blacklisting with Redis for better security.
    """
    # TODO: Add token to blacklist in Redis
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password (requires current password).
    """
    identity_service = IdentityService(db)

    # Verify current password
    if not identity_service.verify_password(
        password_data.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    new_hashed_password = identity_service.hash_password(password_data.new_password)
    current_user.hashed_password = new_hashed_password

    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Useful for verifying token validity and getting user details.
    """
    from app.schemas.user import UserResponse
    return UserResponse.model_validate(current_user)
