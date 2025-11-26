"""
Social features: follow users, activity feed, sharing.

Features:
- Follow/unfollow users
- Activity feed (see what friends are doing)
- Share achievements and insights
- Social stats (followers, following)
- Privacy controls
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SocialService:
    """Service for social features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def follow_user(
        self,
        follower_id: UUID,
        following_id: UUID
    ) -> bool:
        """
        Follow a user.

        Returns True if newly followed, False if already following.
        """
        from app.models.social import Follow

        if follower_id == following_id:
            raise HTTPException(400, "Cannot follow yourself")

        # Check if already following
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return False

        # Create follow relationship
        follow = Follow(
            id=uuid4(),
            follower_id=follower_id,
            following_id=following_id,
            created_at=datetime.utcnow()
        )

        self.db.add(follow)
        await self.db.commit()

        # Create activity
        await self._create_activity(
            user_id=follower_id,
            activity_type="follow",
            target_user_id=following_id
        )

        logger.info(f"User {follower_id} followed {following_id}")

        return True

    async def unfollow_user(
        self,
        follower_id: UUID,
        following_id: UUID
    ):
        """Unfollow a user."""
        from app.models.social import Follow
        from sqlalchemy import delete

        result = await self.db.execute(
            delete(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        )

        if result.rowcount == 0:
            raise HTTPException(404, "Not following this user")

        await self.db.commit()

        logger.info(f"User {follower_id} unfollowed {following_id}")

    async def is_following(
        self,
        follower_id: UUID,
        following_id: UUID
    ) -> bool:
        """Check if user is following another user."""
        from app.models.social import Follow

        result = await self.db.execute(
            select(func.count(Follow.id)).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        )

        count = result.scalar()
        return count > 0

    async def get_followers(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of followers."""
        from app.models.social import Follow
        from app.models.user import User

        result = await self.db.execute(
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .limit(limit)
            .offset(offset)
        )

        users = result.scalars().all()

        return [
            {
                "id": str(user.id),
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url
            }
            for user in users
        ]

    async def get_following(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of users being followed."""
        from app.models.social import Follow
        from app.models.user import User

        result = await self.db.execute(
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .limit(limit)
            .offset(offset)
        )

        users = result.scalars().all()

        return [
            {
                "id": str(user.id),
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url
            }
            for user in users
        ]

    async def get_social_stats(
        self,
        user_id: UUID
    ) -> Dict[str, int]:
        """Get social statistics for a user."""
        from app.models.social import Follow

        # Count followers
        result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.following_id == user_id)
        )
        followers_count = result.scalar() or 0

        # Count following
        result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        )
        following_count = result.scalar() or 0

        return {
            "followers": followers_count,
            "following": following_count
        }

    async def get_activity_feed(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get activity feed for a user.

        Shows activities from users they follow.
        """
        from app.models.social import Activity, Follow

        # Get users being followed
        result = await self.db.execute(
            select(Follow.following_id).where(Follow.follower_id == user_id)
        )
        following_ids = [row[0] for row in result.fetchall()]

        # Include own activities
        following_ids.append(user_id)

        # Get activities
        result = await self.db.execute(
            select(Activity)
            .where(Activity.user_id.in_(following_ids))
            .order_by(Activity.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        activities = result.scalars().all()

        return [
            {
                "id": str(activity.id),
                "user_id": str(activity.user_id),
                "activity_type": activity.activity_type,
                "content": activity.content,
                "metadata": activity.metadata,
                "created_at": activity.created_at.isoformat()
            }
            for activity in activities
        ]

    async def _create_activity(
        self,
        user_id: UUID,
        activity_type: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        target_user_id: Optional[UUID] = None
    ):
        """Create an activity entry."""
        from app.models.social import Activity

        activity = Activity(
            id=uuid4(),
            user_id=user_id,
            activity_type=activity_type,
            content=content,
            metadata=metadata or {},
            target_user_id=target_user_id,
            created_at=datetime.utcnow()
        )

        self.db.add(activity)
        await self.db.commit()

    async def share_achievement(
        self,
        user_id: UUID,
        achievement_type: str,
        achievement_data: Dict[str, Any]
    ):
        """Share an achievement to activity feed."""
        await self._create_activity(
            user_id=user_id,
            activity_type="achievement",
            content=f"Unlocked achievement: {achievement_data.get('name')}",
            metadata=achievement_data
        )

    async def share_insight(
        self,
        user_id: UUID,
        insight_id: UUID,
        insight_title: str
    ):
        """Share an insight to activity feed."""
        await self._create_activity(
            user_id=user_id,
            activity_type="insight_shared",
            content=f"Shared insight: {insight_title}",
            metadata={"insight_id": str(insight_id)}
        )

    async def get_suggested_users(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get suggested users to follow.

        Based on:
        - Users followed by people you follow
        - Popular users
        - Similar interests
        """
        from app.models.social import Follow
        from app.models.user import User

        # Get users followed by people you follow (friends of friends)
        result = await self.db.execute(
            select(User.id, func.count(Follow.id).label("mutual_count"))
            .join(Follow, Follow.following_id == User.id)
            .where(
                Follow.follower_id.in_(
                    select(Follow.following_id).where(Follow.follower_id == user_id)
                ),
                User.id != user_id,  # Not self
                ~User.id.in_(  # Not already following
                    select(Follow.following_id).where(Follow.follower_id == user_id)
                )
            )
            .group_by(User.id)
            .order_by(func.count(Follow.id).desc())
            .limit(limit)
        )

        suggested_ids = [row[0] for row in result.fetchall()]

        # Get user details
        result = await self.db.execute(
            select(User).where(User.id.in_(suggested_ids))
        )
        users = result.scalars().all()

        return [
            {
                "id": str(user.id),
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "reason": "Followed by people you follow"
            }
            for user in users
        ]


# Activity types for feed
class ActivityType:
    FOLLOW = "follow"
    EVENT_CREATED = "event_created"
    ACHIEVEMENT_UNLOCKED = "achievement"
    MILESTONE_REACHED = "milestone"
    INSIGHT_SHARED = "insight_shared"
    GOAL_COMPLETED = "goal_completed"
