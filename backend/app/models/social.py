"""
Social Features Models - Friends, Groups, Challenges, Accountability

Community and social engagement features.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.models.base import Base


class FriendshipStatus(str, Enum):
    """Friendship status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class GroupRole(str, Enum):
    """Group member role"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class GroupPrivacy(str, Enum):
    """Group privacy settings"""
    PUBLIC = "public"  # Anyone can join
    PRIVATE = "private"  # Invite only
    SECRET = "secret"  # Not discoverable


class ChallengeType(str, Enum):
    """Challenge type"""
    SOLO = "solo"
    GROUP = "group"
    ONE_ON_ONE = "one_on_one"


# Association table for group members
group_members = Table(
    'group_members',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('role', SQLEnum(GroupRole), default=GroupRole.MEMBER),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('left_at', DateTime, nullable=True),
    UniqueConstraint('group_id', 'user_id', name='unique_group_member')
)


# Association table for challenge participants
challenge_participants = Table(
    'challenge_participants',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('challenge_id', Integer, ForeignKey('community_challenges.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('progress', Integer, default=0),  # % completion
    Column('is_completed', Boolean, default=False),
    UniqueConstraint('challenge_id', 'user_id', name='unique_challenge_participant')
)


class Friendship(Base):
    """
    Friendship connections between users.
    """
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)

    # Users
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(SQLEnum(FriendshipStatus), default=FriendshipStatus.PENDING)

    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    blocked_at = Column(DateTime, nullable=True)

    # Settings
    share_stats = Column(Boolean, default=True)  # Share basic stats
    share_events = Column(Boolean, default=False)  # Share life events

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('requester_id', 'addressee_id', name='unique_friendship'),
    )

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="friendship_requests_sent")
    addressee = relationship("User", foreign_keys=[addressee_id], back_populates="friendship_requests_received")


class Group(Base):
    """
    User groups for community building.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)

    # Group details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String, nullable=True)

    # Privacy
    privacy = Column(SQLEnum(GroupPrivacy), default=GroupPrivacy.PUBLIC)

    # Settings
    max_members = Column(Integer, default=100)
    allow_member_posts = Column(Boolean, default=True)

    # Category
    category = Column(String, nullable=True)  # e.g., "fitness", "productivity", "mindfulness"

    # Stats
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = relationship("GroupPost", back_populates="group", cascade="all, delete-orphan")
    challenges = relationship("CommunityChallenge", back_populates="group")


class GroupPost(Base):
    """
    Posts within groups.
    """
    __tablename__ = "group_posts"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)

    # Engagement
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # Moderation
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="posts")
    author = relationship("User", back_populates="group_posts")
    comments = relationship("GroupPostComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("GroupPostLike", back_populates="post", cascade="all, delete-orphan")


class GroupPostComment(Base):
    """
    Comments on group posts.
    """
    __tablename__ = "group_post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("group_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    content = Column(Text, nullable=False)

    # Moderation
    is_deleted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    post = relationship("GroupPost", back_populates="comments")
    author = relationship("User", back_populates="group_comments")


class GroupPostLike(Base):
    """
    Likes on group posts.
    """
    __tablename__ = "group_post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("group_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='unique_post_like'),
    )

    # Relationships
    post = relationship("GroupPost", back_populates="likes")
    user = relationship("User", back_populates="group_likes")


class AccountabilityPartnership(Base):
    """
    Accountability partners for mutual support.
    """
    __tablename__ = "accountability_partnerships"

    id = Column(Integer, primary_key=True, index=True)

    # Partners
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Partnership details
    partnership_name = Column(String, nullable=True)  # e.g., "Fitness Buddies"
    goal = Column(Text, nullable=True)  # Shared goal
    check_in_frequency = Column(String, default="daily")  # daily, weekly, monthly

    # Status
    is_active = Column(Boolean, default=True)

    # Stats
    total_check_ins = Column(Integer, default=0)
    last_check_in_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_partnership'),
    )

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="accountability_partnerships_initiated")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="accountability_partnerships_received")
    check_ins = relationship("AccountabilityCheckIn", back_populates="partnership", cascade="all, delete-orphan")


class AccountabilityCheckIn(Base):
    """
    Check-ins between accountability partners.
    """
    __tablename__ = "accountability_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    partnership_id = Column(Integer, ForeignKey("accountability_partnerships.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Check-in content
    message = Column(Text, nullable=True)
    mood = Column(Integer, nullable=True)  # 1-10
    progress_rating = Column(Integer, nullable=True)  # 1-10

    # Response
    partner_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    partnership = relationship("AccountabilityPartnership", back_populates="check_ins")
    user = relationship("User", back_populates="accountability_check_ins")


class CommunityChallenge(Base):
    """
    Community challenges (group or 1-on-1).
    """
    __tablename__ = "community_challenges"

    id = Column(Integer, primary_key=True, index=True)

    # Challenge details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    challenge_type = Column(SQLEnum(ChallengeType), nullable=False)

    # Requirements
    goal_type = Column(String, nullable=False)  # e.g., "streak", "total_count", "target_value"
    goal_metric = Column(String, nullable=False)  # e.g., "exercise", "meditation"
    goal_target = Column(Integer, nullable=False)  # Target value

    # Duration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    duration_days = Column(Integer, nullable=False)

    # Group (if group challenge)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    # Creator
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Settings
    is_public = Column(Boolean, default=True)
    max_participants = Column(Integer, nullable=True)

    # Stats
    participant_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="challenges")
    creator = relationship("User", back_populates="created_challenges")


# Update User model to include social relationships
"""
Add to User class in app/models/user.py:

    # Social - Friendships
    friendship_requests_sent = relationship("Friendship", foreign_keys="Friendship.requester_id", back_populates="requester")
    friendship_requests_received = relationship("Friendship", foreign_keys="Friendship.addressee_id", back_populates="addressee")

    # Social - Groups
    group_posts = relationship("GroupPost", back_populates="author")
    group_comments = relationship("GroupPostComment", back_populates="author")
    group_likes = relationship("GroupPostLike", back_populates="user")

    # Social - Accountability
    accountability_partnerships_initiated = relationship("AccountabilityPartnership", foreign_keys="AccountabilityPartnership.user1_id", back_populates="user1")
    accountability_partnerships_received = relationship("AccountabilityPartnership", foreign_keys="AccountabilityPartnership.user2_id", back_populates="user2")
    accountability_check_ins = relationship("AccountabilityCheckIn", back_populates="user")

    # Social - Challenges
    created_challenges = relationship("CommunityChallenge", back_populates="creator")
"""
