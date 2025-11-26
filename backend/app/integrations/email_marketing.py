"""
Email Marketing Integration (Mailchimp/SendGrid Marketing Campaigns).

Features:
- Contact list management
- Email campaign creation
- Automated sequences
- Analytics and tracking
- Segmentation based on user behavior
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MailchimpClient:
    """
    Mailchimp API client for email marketing.

    Features:
    - Audience management
    - Campaign creation and scheduling
    - Automation workflows
    - Analytics and reports
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'MAILCHIMP_API_KEY', None)
        # Extract datacenter from API key (e.g., us1, us2)
        self.datacenter = self.api_key.split('-')[-1] if self.api_key else 'us1'
        self.base_url = f"https://{self.datacenter}.api.mailchimp.com/3.0"

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request to Mailchimp API."""
        url = f"{self.base_url}/{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                auth=("apikey", self.api_key),
                **kwargs
            )

            response.raise_for_status()
            return response.json() if response.content else {}

    async def add_or_update_member(
        self,
        list_id: str,
        email: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add or update member in audience list.

        Args:
            list_id: Mailchimp audience/list ID
            email: Email address
            data: Member data (merge fields, tags, etc.)

        Returns:
            Member data
        """
        import hashlib
        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()

        payload = {
            "email_address": email,
            "status_if_new": "subscribed",
            **data
        }

        return await self._make_request(
            "PUT",
            f"lists/{list_id}/members/{subscriber_hash}",
            json=payload
        )

    async def add_tags(
        self,
        list_id: str,
        email: str,
        tags: List[str]
    ):
        """Add tags to a member."""
        import hashlib
        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()

        payload = {
            "tags": [{"name": tag, "status": "active"} for tag in tags]
        }

        return await self._make_request(
            "POST",
            f"lists/{list_id}/members/{subscriber_hash}/tags",
            json=payload
        )

    async def create_campaign(
        self,
        list_id: str,
        subject: str,
        from_name: str,
        reply_to: str,
        html_content: str
    ) -> Dict[str, Any]:
        """
        Create email campaign.

        Args:
            list_id: Audience list ID
            subject: Email subject
            from_name: Sender name
            reply_to: Reply-to email
            html_content: HTML email content

        Returns:
            Campaign data
        """
        payload = {
            "type": "regular",
            "recipients": {
                "list_id": list_id
            },
            "settings": {
                "subject_line": subject,
                "from_name": from_name,
                "reply_to": reply_to,
                "title": f"Campaign: {subject}"
            }
        }

        # Create campaign
        campaign = await self._make_request("POST", "campaigns", json=payload)

        # Set content
        await self._make_request(
            "PUT",
            f"campaigns/{campaign['id']}/content",
            json={"html": html_content}
        )

        return campaign

    async def send_campaign(self, campaign_id: str):
        """Send campaign immediately."""
        return await self._make_request("POST", f"campaigns/{campaign_id}/actions/send")

    async def schedule_campaign(self, campaign_id: str, send_at: datetime):
        """Schedule campaign for later."""
        payload = {
            "schedule_time": send_at.isoformat()
        }

        return await self._make_request(
            "POST",
            f"campaigns/{campaign_id}/actions/schedule",
            json=payload
        )


class SendGridMarketingClient:
    """
    SendGrid Marketing Campaigns API client.

    Alternative to Mailchimp for email marketing.
    """

    BASE_URL = "https://api.sendgrid.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'SENDGRID_API_KEY', None)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request to SendGrid API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **kwargs.pop("headers", {})
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                **kwargs
            )

            response.raise_for_status()
            return response.json() if response.content else {}

    async def add_or_update_contact(
        self,
        email: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add or update contact in SendGrid."""
        payload = {
            "contacts": [
                {
                    "email": email,
                    **data
                }
            ]
        }

        return await self._make_request("PUT", "marketing/contacts", json=payload)

    async def add_contact_to_list(self, contact_id: str, list_ids: List[str]):
        """Add contact to lists."""
        payload = {
            "list_ids": list_ids
        }

        return await self._make_request(
            "PUT",
            f"marketing/contacts/{contact_id}/lists",
            json=payload
        )

    async def create_single_send(
        self,
        name: str,
        subject: str,
        html_content: str,
        list_ids: List[str],
        sender_id: int
    ) -> Dict[str, Any]:
        """
        Create single send campaign.

        Args:
            name: Campaign name
            subject: Email subject
            html_content: HTML content
            list_ids: Recipient list IDs
            sender_id: Verified sender ID

        Returns:
            Campaign data
        """
        payload = {
            "name": name,
            "send_to": {
                "list_ids": list_ids
            },
            "email_config": {
                "subject": subject,
                "html_content": html_content,
                "sender_id": sender_id,
                "suppression_group_id": 1  # Unsubscribe group
            }
        }

        return await self._make_request("POST", "marketing/singlesends", json=payload)

    async def schedule_single_send(self, send_id: str, send_at: datetime):
        """Schedule single send for later."""
        payload = {
            "send_at": send_at.isoformat()
        }

        return await self._make_request(
            "PUT",
            f"marketing/singlesends/{send_id}/schedule",
            json=payload
        )


class EmailMarketingService:
    """
    Service for managing email marketing campaigns.

    Features:
    - User lifecycle emails (welcome, onboarding, engagement)
    - Behavior-based segmentation
    - Automated email sequences
    - Campaign analytics
    """

    def __init__(self, db: AsyncSession, provider: str = "mailchimp"):
        self.db = db
        self.provider = provider

        if provider == "mailchimp":
            self.client = MailchimpClient()
            self.list_id = getattr(settings, 'MAILCHIMP_AUDIENCE_ID', None)
        elif provider == "sendgrid":
            self.client = SendGridMarketingClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def subscribe_user(
        self,
        user_id: UUID,
        email: str,
        full_name: str,
        tags: Optional[List[str]] = None
    ):
        """
        Subscribe user to email list.

        Args:
            user_id: User UUID
            email: Email address
            full_name: User's full name
            tags: Optional tags for segmentation
        """
        if self.provider == "mailchimp":
            # Add to Mailchimp
            data = {
                "merge_fields": {
                    "FNAME": full_name.split()[0] if full_name else "",
                    "LNAME": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
                    "USER_ID": str(user_id)
                }
            }

            await self.client.add_or_update_member(self.list_id, email, data)

            # Add tags
            if tags:
                await self.client.add_tags(self.list_id, email, tags)

        elif self.provider == "sendgrid":
            # Add to SendGrid
            data = {
                "first_name": full_name.split()[0] if full_name else "",
                "last_name": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
                "custom_fields": {
                    "user_id": str(user_id)
                }
            }

            await self.client.add_or_update_contact(email, data)

        logger.info(f"Subscribed user {user_id} to email marketing: {email}")

    async def trigger_welcome_sequence(self, email: str):
        """
        Trigger welcome email sequence for new user.

        This would typically be set up as an automation in Mailchimp/SendGrid.
        """
        # Tag user to trigger automation
        if self.provider == "mailchimp":
            await self.client.add_tags(self.list_id, email, ["new_user", "welcome_sequence"])

        logger.info(f"Triggered welcome sequence for {email}")

    async def send_weekly_digest(
        self,
        recipients: List[str],
        subject: str,
        html_content: str
    ):
        """Send weekly digest campaign."""
        if self.provider == "mailchimp":
            campaign = await self.client.create_campaign(
                list_id=self.list_id,
                subject=subject,
                from_name="Aurora Life",
                reply_to="noreply@auroralife.app",
                html_content=html_content
            )

            # Send immediately
            await self.client.send_campaign(campaign['id'])

        logger.info(f"Sent weekly digest to {len(recipients)} recipients")

    async def segment_users_by_engagement(self) -> Dict[str, List[str]]:
        """
        Segment users by engagement level.

        Returns:
            Dict with engagement segments
        """
        from app.models.user import User
        from app.models.event import Event
        from sqlalchemy import func, select
        from datetime import timedelta

        # Get users with event counts in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(
                User.email,
                func.count(Event.id).label("event_count")
            )
            .join(Event, Event.user_id == User.id, isouter=True)
            .where(Event.event_time >= thirty_days_ago)
            .group_by(User.id, User.email)
        )

        segments = {
            "highly_engaged": [],
            "moderately_engaged": [],
            "low_engagement": [],
            "inactive": []
        }

        for row in result.fetchall():
            email = row[0]
            count = row[1]

            if count >= 20:
                segments["highly_engaged"].append(email)
            elif count >= 10:
                segments["moderately_engaged"].append(email)
            elif count >= 1:
                segments["low_engagement"].append(email)
            else:
                segments["inactive"].append(email)

        return segments

    async def send_re_engagement_campaign(self):
        """Send re-engagement campaign to inactive users."""
        segments = await self.segment_users_by_engagement()
        inactive_users = segments["inactive"]

        if not inactive_users:
            logger.info("No inactive users to re-engage")
            return

        html_content = """
        <html>
        <body>
            <h1>We miss you! 👋</h1>
            <p>It's been a while since you've logged into Aurora Life.</p>
            <p>Here's what you're missing:</p>
            <ul>
                <li>🤖 AI-powered insights about your life patterns</li>
                <li>📊 Beautiful data visualizations</li>
                <li>🎯 Goal tracking and achievement</li>
            </ul>
            <p><a href="https://auroralife.app/dashboard">Come back and see your insights</a></p>
        </body>
        </html>
        """

        if self.provider == "mailchimp":
            # Tag inactive users for re-engagement campaign
            for email in inactive_users:
                await self.client.add_tags(self.list_id, email, ["inactive", "re_engagement"])

            # Create and send campaign
            campaign = await self.client.create_campaign(
                list_id=self.list_id,
                subject="We miss you at Aurora Life! 🌅",
                from_name="Aurora Life Team",
                reply_to="hello@auroralife.app",
                html_content=html_content
            )

            await self.client.send_campaign(campaign['id'])

        logger.info(f"Sent re-engagement campaign to {len(inactive_users)} inactive users")


# Celery task for scheduled campaigns
"""
from app.integrations.email_marketing import EmailMarketingService

@celery_app.task
async def send_weekly_digest_task():
    async with async_session() as db:
        service = EmailMarketingService(db)

        # Generate digest content
        html_content = generate_weekly_digest()

        # Get all subscribed users
        recipients = await get_subscribed_users(db)

        await service.send_weekly_digest(
            recipients=[u.email for u in recipients],
            subject="Your Aurora Life Weekly Digest 📊",
            html_content=html_content
        )

@celery_app.task
async def send_re_engagement_campaign_task():
    async with async_session() as db:
        service = EmailMarketingService(db)
        await service.send_re_engagement_campaign()
"""
