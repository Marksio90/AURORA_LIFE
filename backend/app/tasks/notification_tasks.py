"""
Notification background tasks - Email, push notifications, etc.
"""
from celery import shared_task
from typing import Dict, Any
import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.database import async_session

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.notification_tasks.send_email")
def send_email(to: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
    """
    Send email notification using EmailService.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        html_body: Optional HTML body

    Returns:
        Send status
    """
    async def _send():
        from app.services.email_service import EmailService

        async with async_session() as db:
            email_service = EmailService(db)

            success = await email_service._send_email(
                to_email=to,
                subject=subject,
                text_content=body,
                html_content=html_body
            )

            return {
                'success': success,
                'to': to,
                'subject': subject
            }

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.notification_tasks.send_push_notification")
def send_push_notification(user_id: int, title: str, message: str) -> Dict[str, Any]:
    """
    Send push notification to user's devices.

    Args:
        user_id: User ID
        title: Notification title
        message: Notification message

    Returns:
        Send status
    """
    # TODO: Implement push notifications (FCM, APNS)
    # For now, just log the notification
    logger.info(f"[PUSH NOTIFICATION] User {user_id}: {title} - {message}")

    return {
        'success': True,
        'user_id': user_id,
        'title': title,
        'message': 'Push notification logged (FCM/APNS not configured)'
    }


@celery_app.task(name="app.tasks.notification_tasks.send_daily_summary")
def send_daily_summary(user_id: int) -> Dict[str, Any]:
    """
    Generate and send daily summary email to user.

    Args:
        user_id: User ID

    Returns:
        Send status
    """
    async def _send_summary():
        from app.services.email_service import EmailService
        from app.ai.datagenius import DataGeniusService
        from app.models.user import User

        async with async_session() as db:
            try:
                # Get user
                user = await db.get(User, user_id)
                if not user:
                    return {
                        'success': False,
                        'user_id': user_id,
                        'error': 'User not found'
                    }

                # Generate insights
                datagenius = DataGeniusService(db)
                analysis = await datagenius.analyze_user_patterns(user_id, days=1)

                if analysis.get("message") == "No data available for analysis":
                    logger.info(f"No data for daily summary: user {user_id}")
                    return {
                        'success': False,
                        'user_id': user_id,
                        'message': 'Insufficient data for summary'
                    }

                # Get predictions
                energy_pred = await datagenius.predict_energy(user_id, "morning")
                mood_pred = await datagenius.predict_mood(user_id)

                # Prepare email content
                subject = f"Your Daily Aurora Summary - {analysis.get('analyzed_at', '')}"

                text_content = f"""
Hi {user.full_name or user.username},

Here's your Aurora Life Compass daily summary:

📊 Yesterday's Insights:
• Overall Wellbeing: {analysis['scores'].get('overall_wellbeing', 0) * 10:.1f}/10
• Energy: {analysis['scores'].get('energy_score', 0) * 10:.1f}/10
• Mood: {analysis['scores'].get('mood_score', 0) * 10:.1f}/10
• Health: {analysis['scores'].get('health_score', 0) * 10:.1f}/10

🔮 Tomorrow's Predictions:
• Morning Energy: {energy_pred.get('predicted_energy', 5):.1f}/10
• Mood: {mood_pred.get('predicted_mood_score', 5):.1f}/10

💡 Top Insights:
{chr(10).join('• ' + insight for insight in analysis.get('insights', [])[:3])}

Keep tracking your life events to get better insights!

Best regards,
Aurora Life Compass
                """.strip()

                # Send email
                email_service = EmailService(db)
                success = await email_service._send_email(
                    to_email=user.email,
                    subject=subject,
                    text_content=text_content
                )

                return {
                    'success': success,
                    'user_id': user_id,
                    'type': 'daily_summary'
                }

            except Exception as e:
                logger.error(f"Failed to send daily summary for user {user_id}: {e}")
                return {
                    'success': False,
                    'user_id': user_id,
                    'error': str(e)
                }

    return asyncio.run(_send_summary())
