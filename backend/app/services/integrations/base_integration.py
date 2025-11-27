"""
Base Integration Service

Abstract base class for all integrations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import UserIntegration, IntegrationSyncLog, SyncedData, SyncStatus


class BaseIntegration(ABC):
    """
    Abstract base class for integration services.

    All integration providers should inherit from this.
    """

    # Override in subclasses
    PROVIDER_NAME: str = "base"
    INTEGRATION_TYPE: str = "base"
    SUPPORTS_OAUTH: bool = True
    SUPPORTS_WEBHOOKS: bool = False
    DEFAULT_SYNC_FREQUENCY_MINUTES: int = 60

    def __init__(self, db: AsyncSession, user_integration: UserIntegration):
        """
        Initialize integration.

        Args:
            db: Database session
            user_integration: UserIntegration model instance
        """
        self.db = db
        self.user_integration = user_integration
        self.user_id = user_integration.user_id

    @abstractmethod
    async def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Complete OAuth authorization.

        Args:
            auth_code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in authorization

        Returns:
            Authorization result with tokens
        """
        pass

    @abstractmethod
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token.

        Returns:
            New token data
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test if connection is working.

        Returns:
            Connection test result
        """
        pass

    @abstractmethod
    async def sync_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Sync data from external service.

        Args:
            start_date: Start of date range to sync
            end_date: End of date range to sync

        Returns:
            Sync result with stats
        """
        pass

    @abstractmethod
    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect and revoke authorization.

        Returns:
            Disconnection result
        """
        pass

    # Common helper methods

    async def _create_sync_log(
        self,
        sync_type: str = "incremental"
    ) -> IntegrationSyncLog:
        """Create a sync log entry."""
        sync_log = IntegrationSyncLog(
            integration_id=self.user_integration.id,
            sync_status=SyncStatus.IN_PROGRESS,
            sync_type=sync_type,
            started_at=datetime.utcnow()
        )

        self.db.add(sync_log)
        await self.db.commit()
        await self.db.refresh(sync_log)

        return sync_log

    async def _complete_sync_log(
        self,
        sync_log: IntegrationSyncLog,
        success: bool,
        records_created: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
        error_message: Optional[str] = None
    ):
        """Complete a sync log entry."""
        sync_log.completed_at = datetime.utcnow()
        sync_log.sync_status = SyncStatus.COMPLETED if success else SyncStatus.FAILED
        sync_log.records_synced = records_created + records_updated
        sync_log.records_created = records_created
        sync_log.records_updated = records_updated
        sync_log.records_failed = records_failed

        if error_message:
            sync_log.error_message = error_message

        await self.db.commit()

    async def _store_synced_data(
        self,
        data_type: str,
        raw_data: Dict[str, Any],
        data_timestamp: datetime,
        external_id: Optional[str] = None
    ) -> SyncedData:
        """Store synced data."""
        synced_data = SyncedData(
            user_id=self.user_id,
            integration_id=self.user_integration.id,
            data_type=data_type,
            external_id=external_id,
            raw_data=raw_data,
            data_timestamp=data_timestamp,
            is_processed=False
        )

        self.db.add(synced_data)
        await self.db.commit()
        await self.db.refresh(synced_data)

        return synced_data

    async def _check_token_expiry(self) -> bool:
        """Check if access token is expired."""
        if not self.user_integration.token_expires_at:
            return False

        # Consider expired if expires in next 5 minutes
        return datetime.utcnow() >= (self.user_integration.token_expires_at - timedelta(minutes=5))

    async def _ensure_valid_token(self):
        """Ensure we have a valid access token."""
        if await self._check_token_expiry():
            await self.refresh_access_token()

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """
        Get OAuth authorization URL.

        Override in subclasses that support OAuth.

        Args:
            redirect_uri: Where to redirect after authorization
            state: Optional state parameter

        Returns:
            Authorization URL
        """
        raise NotImplementedError("Override in subclass if OAuth is supported")

    async def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook.

        Override in subclasses that support webhooks.

        Args:
            event_type: Type of webhook event
            payload: Webhook payload

        Returns:
            Processing result
        """
        raise NotImplementedError("Override in subclass if webhooks are supported")
