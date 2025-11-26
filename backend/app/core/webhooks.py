"""
Webhook system for external integrations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import hashlib
import hmac
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


class Webhook(Base):
    """Webhook configuration model."""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(100))  # For HMAC signing
    events = Column(JSON, default=list)  # List of event types to subscribe to
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=10)


class WebhookDelivery(Base):
    """Webhook delivery log."""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, index=True)
    event_type = Column(String(100))
    payload = Column(JSON)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivered_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)


class WebhookManager:
    """
    Manage webhook deliveries and subscriptions.

    Features:
    - HMAC signature verification
    - Retry logic with exponential backoff
    - Delivery logging
    - Event filtering
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_webhooks(
        self,
        user_id: int,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """
        Trigger all webhooks subscribed to this event type.

        Args:
            user_id: User ID
            event_type: Type of event (e.g., "event.created")
            payload: Event data
        """
        from sqlalchemy import select

        # Get all active webhooks for this user and event type
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active == True
            )
        )
        webhooks = result.scalars().all()

        # Filter webhooks by event type
        matching_webhooks = [
            wh for wh in webhooks
            if not wh.events or event_type in wh.events
        ]

        # Deliver to each webhook
        for webhook in matching_webhooks:
            await self._deliver_webhook(webhook, event_type, payload)

    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Deliver webhook with retry logic."""
        # Prepare payload
        delivery_payload = {
            "event": event_type,
            "data": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook.id
        }

        # Generate signature if secret is configured
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            signature = self._generate_signature(delivery_payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature

        # Try delivery with retries
        for attempt in range(webhook.retry_count):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook.url,
                        json=delivery_payload,
                        headers=headers,
                        timeout=webhook.timeout_seconds
                    )

                # Log delivery
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=delivery_payload,
                    response_status=response.status_code,
                    response_body=response.text[:1000],  # Limit size
                    success=response.status_code < 400,
                    delivered_at=datetime.utcnow()
                )
                self.db.add(delivery)

                # Update webhook last triggered
                webhook.last_triggered = datetime.utcnow()

                await self.db.commit()

                # Break if successful
                if response.status_code < 400:
                    break

            except Exception as e:
                # Log failed delivery
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=delivery_payload,
                    success=False,
                    error_message=str(e),
                    delivered_at=datetime.utcnow()
                )
                self.db.add(delivery)
                await self.db.commit()

                # Retry with exponential backoff
                if attempt < webhook.retry_count - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        import json

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        expected_sig = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Extract signature from header (format: "sha256=...")
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(signature, expected_sig)
