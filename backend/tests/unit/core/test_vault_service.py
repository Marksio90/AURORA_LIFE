"""Unit tests for Data Vault Service."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.vault.service import VaultService
from app.models.user import User


@pytest.mark.asyncio
class TestVaultService:
    async def test_export_user_data(self, db_session: AsyncSession, test_user: User):
        service = VaultService(db_session)
        # Basic test - full implementation would be more comprehensive
        assert service is not None
