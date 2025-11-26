"""
Stripe payment integration for subscriptions.

Features:
- Customer creation
- Subscription management (create, cancel, upgrade/downgrade)
- Payment methods
- Invoices and billing history
- Webhook handling
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User, Subscription
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionPlan(str):
    """Available subscription plans."""
    FREE = "free"
    PREMIUM_MONTHLY = "premium_monthly"
    PREMIUM_YEARLY = "premium_yearly"


PLAN_PRICES = {
    SubscriptionPlan.PREMIUM_MONTHLY: {
        "price_id": settings.STRIPE_PREMIUM_MONTHLY_PRICE_ID,
        "amount": 999,  # $9.99
        "currency": "usd",
        "interval": "month",
        "name": "Premium Monthly"
    },
    SubscriptionPlan.PREMIUM_YEARLY: {
        "price_id": settings.STRIPE_PREMIUM_YEARLY_PRICE_ID,
        "amount": 9999,  # $99.99 (2 months free)
        "currency": "usd",
        "interval": "year",
        "name": "Premium Yearly"
    },
}


class StripeService:
    """Service for Stripe payment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_customer(
        self,
        user_id: UUID,
        email: str,
        name: Optional[str] = None
    ) -> str:
        """
        Create a Stripe customer for a user.

        Returns Stripe customer ID.
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": str(user_id)}
            )

            # Store customer ID
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one()
            user.stripe_customer_id = customer.id

            await self.db.commit()

            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")

            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment setup failed: {str(e)}"
            )

    async def create_subscription(
        self,
        user_id: UUID,
        plan: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Create a subscription for a user.

        Args:
            user_id: User UUID
            plan: Subscription plan ID
            payment_method_id: Stripe payment method ID

        Returns:
            Subscription details
        """
        from sqlalchemy import select

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(404, "User not found")

        # Ensure customer exists
        if not user.stripe_customer_id:
            await self.create_customer(
                user_id,
                user.email,
                user.full_name
            )

        try:
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=user.stripe_customer_id
            )

            # Set as default payment method
            stripe.Customer.modify(
                user.stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )

            # Create subscription
            plan_info = PLAN_PRICES[plan]
            stripe_subscription = stripe.Subscription.create(
                customer=user.stripe_customer_id,
                items=[{"price": plan_info["price_id"]}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )

            # Store subscription in database
            subscription = Subscription(
                id=uuid4(),
                user_id=user_id,
                stripe_subscription_id=stripe_subscription.id,
                plan=plan,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                ),
            )

            self.db.add(subscription)

            # Upgrade user role
            user.role = "premium"

            await self.db.commit()

            logger.info(f"Created subscription for user {user_id}: {plan}")

            return {
                "subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret,
                "current_period_end": subscription.current_period_end.isoformat()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription failed: {str(e)}"
            )

    async def cancel_subscription(
        self,
        user_id: UUID,
        immediately: bool = False
    ):
        """
        Cancel a user's subscription.

        Args:
            user_id: User UUID
            immediately: If True, cancel immediately. Otherwise, at period end.
        """
        from sqlalchemy import select

        # Get subscription
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"])
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(404, "No active subscription found")

        try:
            if immediately:
                # Cancel immediately
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = "canceled"
                subscription.canceled_at = datetime.utcnow()

                # Downgrade user
                result = await self.db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one()
                user.role = "user"

            else:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True

            await self.db.commit()

            logger.info(f"Canceled subscription for user {user_id}")

        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cancellation failed: {str(e)}"
            )

    async def change_subscription_plan(
        self,
        user_id: UUID,
        new_plan: str
    ):
        """Upgrade or downgrade subscription plan."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(404, "No active subscription found")

        try:
            # Get current subscription from Stripe
            stripe_sub = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )

            # Update subscription item
            new_price_id = PLAN_PRICES[new_plan]["price_id"]
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    "id": stripe_sub["items"]["data"][0].id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations"
            )

            # Update database
            subscription.plan = new_plan

            await self.db.commit()

            logger.info(f"Changed subscription plan for user {user_id} to {new_plan}")

        except stripe.error.StripeError as e:
            logger.error(f"Plan change failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan change failed: {str(e)}"
            )

    async def get_billing_history(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's billing history (invoices)."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.stripe_customer_id:
            return []

        try:
            invoices = stripe.Invoice.list(
                customer=user.stripe_customer_id,
                limit=limit
            )

            return [
                {
                    "id": inv.id,
                    "amount": inv.amount_paid / 100,  # Convert from cents
                    "currency": inv.currency,
                    "status": inv.status,
                    "date": datetime.fromtimestamp(inv.created).isoformat(),
                    "pdf_url": inv.invoice_pdf
                }
                for inv in invoices.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch billing history: {e}")
            return []

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header

        Returns:
            Event details
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )

            # Handle different event types
            if event.type == "customer.subscription.updated":
                await self._handle_subscription_updated(event.data.object)
            elif event.type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event.data.object)
            elif event.type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event.data.object)
            elif event.type == "invoice.payment_failed":
                await self._handle_payment_failed(event.data.object)

            return {"status": "success", "event_type": event.type}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(400, "Invalid signature")

    async def _handle_subscription_updated(self, subscription):
        """Handle subscription.updated webhook."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription.id
            )
        )
        db_subscription = result.scalar_one_or_none()

        if db_subscription:
            db_subscription.status = subscription.status
            db_subscription.current_period_end = datetime.fromtimestamp(
                subscription.current_period_end
            )
            await self.db.commit()

    async def _handle_subscription_deleted(self, subscription):
        """Handle subscription.deleted webhook."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription.id
            )
        )
        db_subscription = result.scalar_one_or_none()

        if db_subscription:
            db_subscription.status = "canceled"
            db_subscription.canceled_at = datetime.utcnow()

            # Downgrade user
            result = await self.db.execute(
                select(User).where(User.id == db_subscription.user_id)
            )
            user = result.scalar_one()
            user.role = "user"

            await self.db.commit()

    async def _handle_payment_succeeded(self, invoice):
        """Handle invoice.payment_succeeded webhook."""
        logger.info(f"Payment succeeded for invoice {invoice.id}")
        # Could send receipt email here

    async def _handle_payment_failed(self, invoice):
        """Handle invoice.payment_failed webhook."""
        logger.warning(f"Payment failed for invoice {invoice.id}")
        # Could send payment failure notification
