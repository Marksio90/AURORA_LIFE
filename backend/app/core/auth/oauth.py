"""
OAuth2 integration with Google and GitHub.

Supports:
- Google OAuth2 (Sign in with Google)
- GitHub OAuth2 (Sign in with GitHub)
- Account linking for existing users
- Automatic user creation for new OAuth users
"""

from typing import Optional, Dict, Any
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.config import settings
from app.models.user import User, OAuthAccount
from app.core.auth.jwt import create_access_token, create_refresh_token
import logging

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """Base class for OAuth2 providers."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth2 authorization URL."""
        raise NotImplementedError

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        raise NotImplementedError

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from provider."""
        raise NotImplementedError


class GoogleOAuth2(OAuth2Provider):
    """Google OAuth2 provider."""

    def __init__(self):
        super().__init__(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo"
        )

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth2 authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query}"

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
            )

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

            data = response.json()
            return data["access_token"]

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                logger.error(f"Google userinfo failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )

            data = response.json()
            return {
                "provider": "google",
                "provider_user_id": data["id"],
                "email": data["email"],
                "email_verified": data.get("verified_email", False),
                "name": data.get("name"),
                "picture": data.get("picture")
            }


class GitHubOAuth2(OAuth2Provider):
    """GitHub OAuth2 provider."""

    def __init__(self):
        super().__init__(
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET,
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user"
        )

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate GitHub OAuth2 authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query}"

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                },
                headers={"Accept": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

            data = response.json()
            return data["access_token"]

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub."""
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                self.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code != 200:
                logger.error(f"GitHub userinfo failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )

            user_data = response.json()

            # Get primary email (if not public)
            email = user_data.get("email")
            if not email:
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )

                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next(
                        (e for e in emails if e["primary"]), None
                    )
                    if primary_email:
                        email = primary_email["email"]

            return {
                "provider": "github",
                "provider_user_id": str(user_data["id"]),
                "email": email,
                "email_verified": True,  # GitHub emails are verified
                "name": user_data.get("name") or user_data.get("login"),
                "picture": user_data.get("avatar_url")
            }


class OAuth2Service:
    """Service for OAuth2 authentication."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = {
            "google": GoogleOAuth2(),
            "github": GitHubOAuth2()
        }

    def get_provider(self, provider: str) -> OAuth2Provider:
        """Get OAuth2 provider by name."""
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown provider: {provider}"
            )
        return self.providers[provider]

    async def authenticate(
        self,
        provider: str,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Authenticate user with OAuth2 provider.

        Returns access token, refresh token, and user info.
        """
        oauth_provider = self.get_provider(provider)

        # Exchange code for access token
        access_token = await oauth_provider.exchange_code(code, redirect_uri)

        # Get user info from provider
        user_info = await oauth_provider.get_user_info(access_token)

        # Find or create user
        user = await self._find_or_create_user(user_info)

        # Create OAuth account link if doesn't exist
        await self._link_oauth_account(user.id, user_info, access_token)

        # Generate JWT tokens
        jwt_access = create_access_token({"sub": str(user.id)})
        jwt_refresh = create_refresh_token({"sub": str(user.id)})

        return {
            "access_token": jwt_access,
            "refresh_token": jwt_refresh,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username
            }
        }

    async def _find_or_create_user(
        self,
        user_info: Dict[str, Any]
    ) -> User:
        """Find existing user or create new one."""
        from sqlalchemy import select

        # Try to find by OAuth account
        result = await self.db.execute(
            select(User).join(OAuthAccount).where(
                OAuthAccount.provider == user_info["provider"],
                OAuthAccount.provider_user_id == user_info["provider_user_id"]
            )
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # Try to find by email
        result = await self.db.execute(
            select(User).where(User.email == user_info["email"])
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create new user
        username = user_info["email"].split("@")[0]
        # Ensure unique username
        base_username = username
        counter = 1
        while True:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            id=uuid4(),
            email=user_info["email"],
            username=username,
            full_name=user_info.get("name"),
            password_hash="",  # OAuth users don't have passwords
            is_active=True,
            is_verified=user_info.get("email_verified", False),
            role="user"
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Created new user via OAuth: {user.email}")

        return user

    async def _link_oauth_account(
        self,
        user_id: uuid4,
        user_info: Dict[str, Any],
        access_token: str
    ):
        """Link OAuth account to user."""
        from sqlalchemy import select

        # Check if link already exists
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.provider == user_info["provider"]
            )
        )
        oauth_account = result.scalar_one_or_none()

        if oauth_account:
            # Update existing
            oauth_account.access_token = access_token
            oauth_account.provider_user_id = user_info["provider_user_id"]
        else:
            # Create new link
            oauth_account = OAuthAccount(
                id=uuid4(),
                user_id=user_id,
                provider=user_info["provider"],
                provider_user_id=user_info["provider_user_id"],
                access_token=access_token
            )
            self.db.add(oauth_account)

        await self.db.commit()


# FastAPI dependency
async def get_oauth_service(db: AsyncSession) -> OAuth2Service:
    """Get OAuth2 service instance."""
    return OAuth2Service(db)
