"""
Email service for user communication using SendGrid
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets
import logging
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid library not installed. Email sending will be mocked.")

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for AURORA_LIFE using SendGrid.

    Features:
    - Email verification
    - Password reset
    - Welcome emails
    - Daily summaries
    - Notifications

    Falls back to logging if SendGrid is not configured.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sendgrid_client = None

        # Initialize SendGrid if API key is available
        if SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("SendGrid email service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
                self.sendgrid_client = None
        else:
            if not SENDGRID_AVAILABLE:
                logger.warning("SendGrid library not available - install with: pip install sendgrid")
            if not settings.SENDGRID_API_KEY:
                logger.info("SENDGRID_API_KEY not set - emails will be logged only")

    async def send_verification_email(self, user_email: str, token: str) -> bool:
        """
        Send email verification link.

        Args:
            user_email: User's email address
            token: Verification token

        Returns:
            True if sent successfully
        """
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        subject = "Verify your Aurora Life Compass account"
        html_content = self._get_verification_email_html(user_email, verification_link)
        text_content = f"""
Welcome to Aurora Life Compass!

Please verify your email address by clicking the link below:
{verification_link}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
Aurora Life Compass Team
        """.strip()

        return await self._send_email(
            to_email=user_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )

    async def send_password_reset_email(self, user_email: str, token: str) -> bool:
        """
        Send password reset link.

        Args:
            user_email: User's email address
            token: Reset token

        Returns:
            True if sent successfully
        """
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        subject = "Reset your Aurora Life Compass password"
        html_content = self._get_password_reset_email_html(user_email, reset_link)
        text_content = f"""
You requested to reset your password for Aurora Life Compass.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
Aurora Life Compass Team
        """.strip()

        return await self._send_email(
            to_email=user_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        subject = f"Welcome to Aurora Life Compass, {user_name}!"
        html_content = self._get_welcome_email_html(user_name)
        text_content = f"""
Hi {user_name},

Welcome to Aurora Life Compass! 🌟

We're excited to have you on board. Aurora is your personal AI-powered life management platform that helps you:

• Track and analyze your life patterns
• Predict your energy and mood
• Get personalized recommendations
• Make better life decisions

Get started by:
1. Log in to your account
2. Add your first life events
3. Explore AI-powered insights

If you have any questions, feel free to reach out to our support team.

Best regards,
Aurora Life Compass Team
        """.strip()

        return await self._send_email(
            to_email=user_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Internal method to send email via SendGrid or log it.

        Args:
            to_email: Recipient email
            subject: Email subject
            text_content: Plain text content
            html_content: HTML content (optional)

        Returns:
            True if sent or logged successfully
        """
        # If SendGrid is configured, send real email
        if self.sendgrid_client:
            try:
                message = Mail(
                    from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
                    to_emails=To(to_email),
                    subject=subject,
                    plain_text_content=Content("text/plain", text_content)
                )

                if html_content:
                    message.add_content(Content("text/html", html_content))

                response = self.sendgrid_client.send(message)

                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email sent successfully to {to_email}: {subject}")
                    return True
                else:
                    logger.error(f"SendGrid returned status {response.status_code} for {to_email}")
                    return False

            except Exception as e:
                logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
                return False

        # Fallback: Log email content
        else:
            logger.info(f"[EMAIL MOCK] To: {to_email}")
            logger.info(f"[EMAIL MOCK] Subject: {subject}")
            logger.debug(f"[EMAIL MOCK] Content:\n{text_content}")
            return True

    def _get_verification_email_html(self, email: str, verification_link: str) -> str:
        """Generate HTML for verification email."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 Aurora Life Compass</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email</h2>
            <p>Welcome to Aurora Life Compass! We're excited to have you on board.</p>
            <p>Please verify your email address to activate your account:</p>
            <p style="text-align: center;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
            <p><small>This link will expire in 24 hours.</small></p>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Aurora Life Compass. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

    def _get_password_reset_email_html(self, email: str, reset_link: str) -> str:
        """Generate HTML for password reset email."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Password Reset</h1>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>You requested to reset your password for Aurora Life Compass.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
            <p><small>This link will expire in 1 hour.</small></p>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong> If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2024 Aurora Life Compass. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

    def _get_welcome_email_html(self, user_name: str) -> str:
        """Generate HTML for welcome email."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #667eea; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 Welcome to Aurora!</h1>
        </div>
        <div class="content">
            <h2>Hi {user_name},</h2>
            <p>Welcome to Aurora Life Compass! We're thrilled to have you on board.</p>
            <p>Aurora is your personal AI-powered life management platform. Here's what you can do:</p>

            <div class="feature">
                <strong>📊 Track Life Patterns</strong><br>
                Record events and let AI discover insights about your life.
            </div>

            <div class="feature">
                <strong>🔮 AI Predictions</strong><br>
                Predict your energy, mood, and productivity using machine learning.
            </div>

            <div class="feature">
                <strong>💡 Smart Recommendations</strong><br>
                Get personalized suggestions from 7 specialized AI agents.
            </div>

            <div class="feature">
                <strong>🎯 What-If Scenarios</strong><br>
                Simulate life changes and see predicted outcomes.
            </div>

            <p style="text-align: center;">
                <a href="{settings.FRONTEND_URL}" class="button">Get Started</a>
            </p>

            <p>Need help? We're here for you. Just reply to this email anytime.</p>

            <p>Best regards,<br>The Aurora Team</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Aurora Life Compass. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

    @staticmethod
    def generate_verification_token() -> str:
        """Generate secure verification token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_reset_token() -> str:
        """Generate secure password reset token."""
        return secrets.token_urlsafe(32)
