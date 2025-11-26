"""
Role-Based Access Control (RBAC) implementation.

Supports:
- Multiple roles (user, premium, admin, super_admin)
- Permission-based access control
- Role hierarchies
- Decorator for route protection
"""

from enum import Enum
from typing import List, Optional, Set
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps

from app.models.user import User
from app.core.auth.dependencies import get_current_user


class Role(str, Enum):
    """User roles with hierarchy."""
    USER = "user"              # Basic user
    PREMIUM = "premium"        # Paid subscription
    MODERATOR = "moderator"    # Content moderation
    ADMIN = "admin"            # System administration
    SUPER_ADMIN = "super_admin"  # Full access


class Permission(str, Enum):
    """Granular permissions."""
    # Events
    EVENT_READ = "event:read"
    EVENT_CREATE = "event:create"
    EVENT_UPDATE = "event:update"
    EVENT_DELETE = "event:delete"

    # Predictions
    PREDICTION_READ = "prediction:read"
    PREDICTION_GENERATE = "prediction:generate"

    # Insights
    INSIGHT_READ = "insight:read"
    INSIGHT_GENERATE = "insight:generate"

    # Users
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Admin
    ADMIN_USERS_MANAGE = "admin:users:manage"
    ADMIN_SYSTEM_CONFIG = "admin:system:config"
    ADMIN_MODEL_RETRAIN = "admin:model:retrain"
    ADMIN_VIEW_AUDIT_LOGS = "admin:audit:view"

    # Premium features
    PREMIUM_AI_INSIGHTS = "premium:ai_insights"
    PREMIUM_ADVANCED_ANALYTICS = "premium:advanced_analytics"
    PREMIUM_API_EXTENDED = "premium:api_extended"
    PREMIUM_EXPORT_DATA = "premium:export_data"


# Role -> Permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.EVENT_READ,
        Permission.EVENT_CREATE,
        Permission.EVENT_UPDATE,
        Permission.EVENT_DELETE,
        Permission.PREDICTION_READ,
        Permission.PREDICTION_GENERATE,
        Permission.INSIGHT_READ,
        Permission.INSIGHT_GENERATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
    },
    Role.PREMIUM: {
        # All USER permissions plus:
        Permission.PREMIUM_AI_INSIGHTS,
        Permission.PREMIUM_ADVANCED_ANALYTICS,
        Permission.PREMIUM_API_EXTENDED,
        Permission.PREMIUM_EXPORT_DATA,
    },
    Role.MODERATOR: {
        # All USER permissions plus:
        Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_VIEW_AUDIT_LOGS,
    },
    Role.ADMIN: {
        # All permissions except super admin
        Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_SYSTEM_CONFIG,
        Permission.ADMIN_MODEL_RETRAIN,
        Permission.ADMIN_VIEW_AUDIT_LOGS,
        Permission.USER_DELETE,
    },
    Role.SUPER_ADMIN: {
        # ALL permissions
        perm for perm in Permission
    },
}

# Role hierarchy (higher roles inherit lower role permissions)
ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: [Role.ADMIN, Role.MODERATOR, Role.PREMIUM, Role.USER],
    Role.ADMIN: [Role.MODERATOR, Role.PREMIUM, Role.USER],
    Role.MODERATOR: [Role.USER],
    Role.PREMIUM: [Role.USER],
    Role.USER: [],
}


class RBACService:
    """Service for role and permission management."""

    @staticmethod
    def get_user_permissions(user: User) -> Set[Permission]:
        """Get all permissions for a user based on their role."""
        user_role = Role(user.role)
        permissions = set()

        # Add role's direct permissions
        permissions.update(ROLE_PERMISSIONS.get(user_role, set()))

        # Add inherited permissions from role hierarchy
        for inherited_role in ROLE_HIERARCHY.get(user_role, []):
            permissions.update(ROLE_PERMISSIONS.get(inherited_role, set()))

        return permissions

    @staticmethod
    def user_has_permission(user: User, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        user_permissions = RBACService.get_user_permissions(user)
        return permission in user_permissions

    @staticmethod
    def user_has_role(user: User, role: Role) -> bool:
        """Check if user has a specific role."""
        user_role = Role(user.role)
        return user_role == role or role in ROLE_HIERARCHY.get(user_role, [])

    @staticmethod
    def check_permission(user: User, permission: Permission):
        """Check permission and raise exception if not authorized."""
        if not RBACService.user_has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}"
            )

    @staticmethod
    def check_role(user: User, role: Role):
        """Check role and raise exception if not authorized."""
        if not RBACService.user_has_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )


# FastAPI dependencies for route protection
def require_permission(permission: Permission):
    """
    Dependency to require a specific permission.

    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_permission(Permission.ADMIN_USERS_MANAGE))])
        async def list_all_users():
            ...
    """
    def permission_checker(user: User = Depends(get_current_user)):
        RBACService.check_permission(user, permission)
        return user
    return permission_checker


def require_role(role: Role):
    """
    Dependency to require a specific role.

    Usage:
        @app.get("/admin/config", dependencies=[Depends(require_role(Role.ADMIN))])
        async def get_config():
            ...
    """
    def role_checker(user: User = Depends(get_current_user)):
        RBACService.check_role(user, role)
        return user
    return role_checker


def require_any_permission(*permissions: Permission):
    """
    Dependency to require ANY of the specified permissions.

    Usage:
        @app.get("/insights", dependencies=[Depends(require_any_permission(
            Permission.INSIGHT_READ,
            Permission.PREMIUM_AI_INSIGHTS
        ))])
        async def get_insights():
            ...
    """
    def permission_checker(user: User = Depends(get_current_user)):
        user_permissions = RBACService.get_user_permissions(user)
        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return permission_checker


def require_all_permissions(*permissions: Permission):
    """
    Dependency to require ALL of the specified permissions.

    Usage:
        @app.post("/admin/retrain", dependencies=[Depends(require_all_permissions(
            Permission.ADMIN_MODEL_RETRAIN,
            Permission.ADMIN_SYSTEM_CONFIG
        ))])
        async def retrain_models():
            ...
    """
    def permission_checker(user: User = Depends(get_current_user)):
        user_permissions = RBACService.get_user_permissions(user)
        if not all(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return permission_checker


# Convenience dependencies
RequireUser = Depends(require_role(Role.USER))
RequirePremium = Depends(require_role(Role.PREMIUM))
RequireModerator = Depends(require_role(Role.MODERATOR))
RequireAdmin = Depends(require_role(Role.ADMIN))
RequireSuperAdmin = Depends(require_role(Role.SUPER_ADMIN))


# Admin route helpers
async def upgrade_user_role(
    user_id: str,
    new_role: Role,
    db: AsyncSession,
    admin_user: User
) -> User:
    """
    Upgrade user's role (admin operation).

    Args:
        user_id: ID of user to upgrade
        new_role: New role to assign
        db: Database session
        admin_user: Admin performing the operation

    Returns:
        Updated user

    Raises:
        HTTPException: If admin lacks permission
    """
    from sqlalchemy import select
    from uuid import UUID

    # Check admin has permission
    RBACService.check_permission(admin_user, Permission.ADMIN_USERS_MANAGE)

    # Super admin can only be set by another super admin
    if new_role == Role.SUPER_ADMIN:
        RBACService.check_role(admin_user, Role.SUPER_ADMIN)

    # Get target user
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update role
    user.role = new_role.value
    await db.commit()
    await db.refresh(user)

    return user


# Example usage in routes:
"""
from fastapi import APIRouter, Depends
from app.core.auth.rbac import RequireAdmin, require_permission, Permission

router = APIRouter()

@router.get("/admin/users", dependencies=[RequireAdmin])
async def list_all_users():
    # Only admins can access
    ...

@router.post(
    "/admin/retrain",
    dependencies=[Depends(require_permission(Permission.ADMIN_MODEL_RETRAIN))]
)
async def retrain_models():
    # Only users with model retrain permission
    ...

@router.get("/premium/insights")
async def get_premium_insights(
    user: User = Depends(require_permission(Permission.PREMIUM_AI_INSIGHTS))
):
    # Only premium users can access
    # user object is available in the route
    ...
"""
