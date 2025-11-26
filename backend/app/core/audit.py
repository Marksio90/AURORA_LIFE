"""
Audit logging system for tracking all important actions.

Logs user actions, data changes, security events, and system operations.
Audit logs are immutable and stored with full context.

Usage:
    from app.core.audit import audit_log, AuditAction

    await audit_log(
        user_id=user.id,
        action=AuditAction.USER_LOGIN,
        resource_type="user",
        resource_id=user.id,
        changes={"ip": request.client.host},
        request=request
    )
"""

from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Predefined audit actions."""

    # Authentication
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    TOKEN_REFRESH = "token.refresh"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_EMAIL_VERIFIED = "user.email_verified"

    # Events
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_BATCH_CREATED = "event.batch_created"

    # Predictions
    PREDICTION_GENERATED = "prediction.generated"
    PREDICTION_VIEWED = "prediction.viewed"

    # Insights
    INSIGHT_GENERATED = "insight.generated"
    INSIGHT_VIEWED = "insight.viewed"
    INSIGHT_DELETED = "insight.deleted"

    # Security
    SECURITY_PASSWORD_RESET_REQUESTED = "security.password_reset_requested"
    SECURITY_PASSWORD_RESET_COMPLETED = "security.password_reset_completed"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    SECURITY_UNAUTHORIZED_ACCESS = "security.unauthorized_access"

    # Admin
    ADMIN_USER_IMPERSONATION = "admin.user_impersonation"
    ADMIN_SETTINGS_CHANGED = "admin.settings_changed"
    ADMIN_MODEL_RETRAINED = "admin.model_retrained"

    # System
    SYSTEM_BACKUP_CREATED = "system.backup_created"
    SYSTEM_MIGRATION_RUN = "system.migration_run"
    SYSTEM_MAINTENANCE_MODE = "system.maintenance_mode"


class AuditLogger:
    """Service for creating audit log entries."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log(
        self,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> UUID:
        """
        Create an audit log entry.

        Args:
            action: The action being audited
            user_id: ID of the user performing the action
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            changes: Dict of what changed (before/after)
            metadata: Additional context
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether the action succeeded
            error_message: Error message if action failed

        Returns:
            UUID of the created audit log entry
        """
        log_id = uuid4()

        audit_entry = {
            "id": log_id,
            "user_id": user_id,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "changes": changes or {},
            "metadata": metadata or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "error_message": error_message,
            "created_at": datetime.now(timezone.utc)
        }

        try:
            await self.db.execute(
                insert("audit_logs").values(**audit_entry)
            )
            await self.db.commit()

            logger.info(
                f"Audit log created: {action.value}",
                extra={
                    "audit_id": str(log_id),
                    "user_id": str(user_id) if user_id else None,
                    "action": action.value
                }
            )

            return log_id

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            await self.db.rollback()
            # Don't raise - audit logging should not break the main flow
            return log_id

    async def log_from_request(
        self,
        action: AuditAction,
        request: Request,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UUID:
        """
        Create audit log from FastAPI request.

        Automatically extracts IP and user agent from request.
        """
        return await self.log(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            **kwargs
        )


# Convenience function for quick audit logging
async def audit_log(
    db_session: AsyncSession,
    action: AuditAction,
    **kwargs
) -> UUID:
    """
    Quick audit log helper.

    Usage:
        await audit_log(
            db_session=db,
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            ip_address=request.client.host
        )
    """
    logger_service = AuditLogger(db_session)
    return await logger_service.log(action=action, **kwargs)


# Dependency for FastAPI routes
async def get_audit_logger(
    db: AsyncSession
) -> AuditLogger:
    """FastAPI dependency for audit logger."""
    return AuditLogger(db)


# Middleware for automatic audit logging of API requests
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit all API requests.

    Logs successful requests and failed requests with error details.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip audit for health checks and metrics
        if request.url.path in ["/health", "/health/ready", "/metrics"]:
            return await call_next(request)

        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        start_time = datetime.now(timezone.utc)

        try:
            response: Response = await call_next(request)

            # Log successful requests
            if response.status_code < 400:
                # Only log mutations (POST, PUT, DELETE, PATCH)
                if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                    action_map = {
                        "POST": "created",
                        "PUT": "updated",
                        "DELETE": "deleted",
                        "PATCH": "updated"
                    }

                    # Extract resource from path
                    path_parts = request.url.path.split("/")
                    resource_type = path_parts[3] if len(path_parts) > 3 else "unknown"
                    resource_id = path_parts[4] if len(path_parts) > 4 else None

                    action = f"{resource_type}.{action_map[request.method]}"

                    # Note: We can't easily get db_session here without dependency injection
                    # This is a placeholder - actual implementation would use background task
                    logger.info(
                        f"Audit: {action}",
                        extra={
                            "user_id": str(user_id) if user_id else None,
                            "method": request.method,
                            "path": request.url.path,
                            "status": response.status_code
                        }
                    )

            return response

        except HTTPException as e:
            # Log failed requests
            logger.warning(
                f"Audit: Request failed",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "method": request.method,
                    "path": request.url.path,
                    "status": e.status_code,
                    "error": e.detail
                }
            )
            raise

        except Exception as e:
            logger.error(
                f"Audit: Request error",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                }
            )
            raise


# Query helpers for audit logs
async def get_user_audit_log(
    db_session: AsyncSession,
    user_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> list:
    """Get audit logs for a specific user."""
    result = await db_session.execute(
        """
        SELECT * FROM audit_logs
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        {"user_id": user_id, "limit": limit, "offset": offset}
    )
    return result.fetchall()


async def get_resource_audit_log(
    db_session: AsyncSession,
    resource_type: str,
    resource_id: UUID,
    limit: int = 100
) -> list:
    """Get audit logs for a specific resource."""
    result = await db_session.execute(
        """
        SELECT * FROM audit_logs
        WHERE resource_type = :resource_type
          AND resource_id = :resource_id
        ORDER BY created_at DESC
        LIMIT :limit
        """,
        {"resource_type": resource_type, "resource_id": resource_id, "limit": limit}
    )
    return result.fetchall()


async def get_security_events(
    db_session: AsyncSession,
    hours: int = 24
) -> list:
    """Get recent security-related audit events."""
    result = await db_session.execute(
        """
        SELECT * FROM audit_logs
        WHERE action LIKE 'security.%'
          AND created_at > NOW() - INTERVAL ':hours hours'
        ORDER BY created_at DESC
        """,
        {"hours": hours}
    )
    return result.fetchall()


# Compliance reporting
async def generate_compliance_report(
    db_session: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Generate compliance report for audit logs.

    Returns summary of all actions in the time period.
    """
    result = await db_session.execute(
        """
        SELECT
            action,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed
        FROM audit_logs
        WHERE created_at BETWEEN :start_date AND :end_date
        GROUP BY action
        ORDER BY count DESC
        """,
        {"start_date": start_date, "end_date": end_date}
    )

    actions = result.fetchall()

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "actions": [
            {
                "action": row[0],
                "total_count": row[1],
                "unique_users": row[2],
                "successful": row[3],
                "failed": row[4]
            }
            for row in actions
        ]
    }
