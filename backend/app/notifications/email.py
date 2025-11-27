"""
Email Notification Service

Sends email notifications using SMTP.
"""
from typing import List, Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "Aurora Life",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.from_name = from_name

    def _create_connection(self) -> smtplib.SMTP:
        """Create SMTP connection"""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()

        if self.smtp_user and self.smtp_password:
            server.login(self.smtp_user, self.smtp_password)

        return server

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add plain text part
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Send
            server = self._create_connection()
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_notification_email(
        self,
        to_email: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
    ) -> bool:
        """
        Send notification email.

        Args:
            to_email: Recipient email
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            action_url: Optional action URL
            action_text: Optional action button text

        Returns:
            bool: True if sent successfully
        """
        html_body = self._render_notification_template(
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            action_text=action_text,
        )

        text_body = f"{title}\n\n{message}"

        if action_url:
            text_body += f"\n\n{action_text or 'View'}: {action_url}"

        return self.send_email(
            to_email=to_email,
            subject=f"Aurora Life: {title}",
            html_body=html_body,
            text_body=text_body,
        )

    def send_daily_digest(
        self,
        to_email: str,
        notifications: List[Dict[str, Any]],
        date: datetime,
    ) -> bool:
        """
        Send daily digest email.

        Args:
            to_email: Recipient email
            notifications: List of notifications
            date: Date for digest

        Returns:
            bool: True if sent successfully
        """
        html_body = self._render_digest_template(
            notifications=notifications,
            date=date,
        )

        return self.send_email(
            to_email=to_email,
            subject=f"Aurora Life Daily Digest - {date.strftime('%B %d, %Y')}",
            html_body=html_body,
        )

    def send_weekly_summary(
        self,
        to_email: str,
        summary_data: Dict[str, Any],
        week_start: datetime,
        week_end: datetime,
    ) -> bool:
        """
        Send weekly summary email.

        Args:
            to_email: Recipient email
            summary_data: Summary data (stats, insights, etc.)
            week_start: Week start date
            week_end: Week end date

        Returns:
            bool: True if sent successfully
        """
        html_body = self._render_weekly_summary_template(
            summary_data=summary_data,
            week_start=week_start,
            week_end=week_end,
        )

        return self.send_email(
            to_email=to_email,
            subject=f"Aurora Life Weekly Summary - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d')}",
            html_body=html_body,
        )

    # ==================== TEMPLATES ====================

    def _render_notification_template(
        self,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
    ) -> str:
        """Render notification email template"""

        # Icon based on type
        icon_map = {
            "insight": "💡",
            "recommendation": "🎯",
            "achievement": "🏆",
            "level_up": "⬆️",
            "streak": "🔥",
            "reminder": "⏰",
            "social": "👥",
            "system": "🔔",
            "alert": "⚠️",
        }
        icon = icon_map.get(notification_type, "🔔")

        action_button = ""
        if action_url and action_text:
            action_button = f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{action_url}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    {action_text}
                </a>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px;">
                <div style="text-align: center; font-size: 48px; margin-bottom: 20px;">
                    {icon}
                </div>

                <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">
                    {title}
                </h2>

                <div style="background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <p style="font-size: 16px; color: #555;">
                        {message}
                    </p>
                </div>

                {action_button}

                <div style="text-align: center; color: #777; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p>Aurora Life - Your Life Tracking Companion</p>
                    <p>
                        <a href="https://aurora-life.com/settings/notifications" style="color: #4CAF50; text-decoration: none;">
                            Notification Settings
                        </a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _render_digest_template(
        self,
        notifications: List[Dict[str, Any]],
        date: datetime,
    ) -> str:
        """Render daily digest email template"""

        notifications_html = ""

        for notif in notifications:
            notifications_html += f"""
            <div style="background-color: white; border-left: 4px solid #4CAF50; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{notif['title']}</h4>
                <p style="margin: 0; color: #555; font-size: 14px;">{notif['message']}</p>
                <small style="color: #999;">{notif.get('created_at', '')}</small>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px;">
                <h2 style="color: #2c3e50; text-align: center; margin-bottom: 10px;">
                    📊 Daily Digest
                </h2>

                <p style="text-align: center; color: #777; margin-bottom: 30px;">
                    {date.strftime('%B %d, %Y')}
                </p>

                <div>
                    {notifications_html}
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://aurora-life.com/dashboard" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        View Dashboard
                    </a>
                </div>

                <div style="text-align: center; color: #777; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p>Aurora Life - Your Life Tracking Companion</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _render_weekly_summary_template(
        self,
        summary_data: Dict[str, Any],
        week_start: datetime,
        week_end: datetime,
    ) -> str:
        """Render weekly summary email template"""

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px;">
                <h2 style="color: #2c3e50; text-align: center; margin-bottom: 10px;">
                    📈 Weekly Summary
                </h2>

                <p style="text-align: center; color: #777; margin-bottom: 30px;">
                    {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}
                </p>

                <div style="background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #4CAF50; margin-top: 0;">Your Week at a Glance</h3>

                    <div style="margin: 20px 0;">
                        <p><strong>Overall Wellness Score:</strong> {summary_data.get('wellness_score', 'N/A')}/100</p>
                        <p><strong>Activities Logged:</strong> {summary_data.get('activities_count', 'N/A')}</p>
                        <p><strong>Achievements Unlocked:</strong> {summary_data.get('achievements', 'N/A')}</p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://aurora-life.com/reports/weekly" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        View Full Report
                    </a>
                </div>

                <div style="text-align: center; color: #777; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p>Aurora Life - Your Life Tracking Companion</p>
                </div>
            </div>
        </body>
        </html>
        """
