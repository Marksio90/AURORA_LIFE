"""Add Phase 8 models (gamification, social, integrations)

Revision ID: 002
Revises: 001
Create Date: 2024-11-27 12:00:00.000000

This migration adds Phase 8 platform features:
- Gamification system (levels, achievements, badges, streaks, challenges, leaderboards)
- Social features (friends, groups, accountability partners, community challenges)
- External integrations (health trackers, calendars, music services)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # ==================== GAMIFICATION TABLES ====================

    # User levels table
    op.create_table(
        'user_levels',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('current_level', sa.Integer(), default=1, nullable=False),
        sa.Column('total_xp', sa.Integer(), default=0, nullable=False),
        sa.Column('xp_to_next_level', sa.Integer(), default=100, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_user_levels_user_id', 'user_levels', ['user_id'])
    op.create_index('idx_user_levels_level', 'user_levels', ['current_level'])
    op.create_index('idx_user_levels_total_xp', 'user_levels', ['total_xp'])

    # Achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # health, social, consistency, milestone
        sa.Column('icon', sa.String(100)),
        sa.Column('points', sa.Integer(), default=100, nullable=False),
        sa.Column('xp_reward', sa.Integer(), default=50, nullable=False),
        sa.Column('rarity', sa.String(20), default='common', nullable=False),  # common, rare, epic, legendary
        sa.Column('requirements', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_achievements_category', 'achievements', ['category'])
    op.create_index('idx_achievements_rarity', 'achievements', ['rarity'])
    op.create_index('idx_achievements_is_active', 'achievements', ['is_active'])

    # User achievements table
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('progress', postgresql.JSONB(), default={}),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
    )
    op.create_index('idx_user_achievements_user_id', 'user_achievements', ['user_id'])
    op.create_index('idx_user_achievements_unlocked_at', 'user_achievements', ['unlocked_at'])

    # Badges table
    op.create_table(
        'badges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(100)),
        sa.Column('color', sa.String(7)),  # Hex color code
        sa.Column('requirements', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_badges_is_active', 'badges', ['is_active'])

    # User badges table
    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )
    op.create_index('idx_user_badges_user_id', 'user_badges', ['user_id'])
    op.create_index('idx_user_badges_earned_at', 'user_badges', ['earned_at'])

    # Streaks table
    op.create_table(
        'streaks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('streak_type', sa.String(50), nullable=False),  # daily_login, exercise, meditation, etc.
        sa.Column('current_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('longest_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'streak_type', name='uq_user_streak_type'),
    )
    op.create_index('idx_streaks_user_id', 'streaks', ['user_id'])
    op.create_index('idx_streaks_type', 'streaks', ['streak_type'])
    op.create_index('idx_streaks_current', 'streaks', ['current_streak'])

    # Daily challenges table
    op.create_table(
        'daily_challenges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(20), default='easy', nullable=False),  # easy, medium, hard
        sa.Column('xp_reward', sa.Integer(), default=50, nullable=False),
        sa.Column('points_reward', sa.Integer(), default=25, nullable=False),
        sa.Column('requirements', postgresql.JSONB(), nullable=False),
        sa.Column('active_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_daily_challenges_date', 'daily_challenges', ['active_date'])
    op.create_index('idx_daily_challenges_is_active', 'daily_challenges', ['is_active'])

    # User challenges table
    op.create_table(
        'user_challenges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), default='active', nullable=False),  # active, completed, failed
        sa.Column('progress', postgresql.JSONB(), default={}),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['challenge_id'], ['daily_challenges.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'challenge_id', name='uq_user_challenge'),
    )
    op.create_index('idx_user_challenges_user_id', 'user_challenges', ['user_id'])
    op.create_index('idx_user_challenges_status', 'user_challenges', ['status'])

    # Leaderboards table
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leaderboard_type', sa.String(50), nullable=False),  # xp, points, streaks
        sa.Column('time_period', sa.String(20), nullable=False),  # daily, weekly, monthly, all_time
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer()),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('is_visible', sa.Boolean(), default=True, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_leaderboards_user_period', 'leaderboards', ['user_id', 'time_period'])
    op.create_index('idx_leaderboards_type_period', 'leaderboards', ['leaderboard_type', 'time_period'])
    op.create_index('idx_leaderboards_rank', 'leaderboards', ['rank'])


    # ==================== SOCIAL TABLES ====================

    # Friendships table
    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('friend_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),  # pending, accepted, blocked
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'friend_id', name='uq_friendship'),
        sa.CheckConstraint('user_id != friend_id', name='check_no_self_friendship'),
    )
    op.create_index('idx_friendships_user_id', 'friendships', ['user_id'])
    op.create_index('idx_friendships_friend_id', 'friendships', ['friend_id'])
    op.create_index('idx_friendships_status', 'friendships', ['status'])

    # Groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('privacy', sa.String(20), default='public', nullable=False),  # public, private, secret
        sa.Column('category', sa.String(50)),
        sa.Column('max_members', sa.Integer(), default=100),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_groups_creator_id', 'groups', ['creator_id'])
    op.create_index('idx_groups_privacy', 'groups', ['privacy'])
    op.create_index('idx_groups_category', 'groups', ['category'])

    # Group memberships table
    op.create_table(
        'group_memberships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), default='member', nullable=False),  # admin, moderator, member
        sa.Column('status', sa.String(20), default='active', nullable=False),  # active, invited, banned
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_membership'),
    )
    op.create_index('idx_group_memberships_group_id', 'group_memberships', ['group_id'])
    op.create_index('idx_group_memberships_user_id', 'group_memberships', ['user_id'])
    op.create_index('idx_group_memberships_status', 'group_memberships', ['status'])

    # Group posts table
    op.create_table(
        'group_posts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_urls', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('is_pinned', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_group_posts_group_id', 'group_posts', ['group_id'])
    op.create_index('idx_group_posts_author_id', 'group_posts', ['author_id'])
    op.create_index('idx_group_posts_created_at', 'group_posts', ['created_at'])
    op.create_index('idx_group_posts_tags_gin', 'group_posts', ['tags'], postgresql_using='gin')

    # Post comments table
    op.create_table(
        'post_comments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['group_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['post_comments.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_post_comments_post_id', 'post_comments', ['post_id'])
    op.create_index('idx_post_comments_author_id', 'post_comments', ['author_id'])
    op.create_index('idx_post_comments_parent_id', 'post_comments', ['parent_comment_id'])

    # Post likes table
    op.create_table(
        'post_likes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['group_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('post_id', 'user_id', name='uq_post_like'),
    )
    op.create_index('idx_post_likes_post_id', 'post_likes', ['post_id'])
    op.create_index('idx_post_likes_user_id', 'post_likes', ['user_id'])

    # Accountability partnerships table
    op.create_table(
        'accountability_partnerships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user1_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user2_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),  # pending, active, ended
        sa.Column('check_in_frequency', sa.String(20), default='daily', nullable=False),
        sa.Column('goals', postgresql.JSONB(), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user1_id', 'user2_id', name='uq_accountability_partnership'),
        sa.CheckConstraint('user1_id < user2_id', name='check_user_order'),
    )
    op.create_index('idx_accountability_partnerships_user1', 'accountability_partnerships', ['user1_id'])
    op.create_index('idx_accountability_partnerships_user2', 'accountability_partnerships', ['user2_id'])
    op.create_index('idx_accountability_partnerships_status', 'accountability_partnerships', ['status'])

    # Partnership check-ins table
    op.create_table(
        'partnership_check_ins',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('partnership_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('mood', sa.String(20)),
        sa.Column('progress', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['partnership_id'], ['accountability_partnerships.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_partnership_check_ins_partnership_id', 'partnership_check_ins', ['partnership_id'])
    op.create_index('idx_partnership_check_ins_user_id', 'partnership_check_ins', ['user_id'])
    op.create_index('idx_partnership_check_ins_created_at', 'partnership_check_ins', ['created_at'])

    # Community challenges table
    op.create_table(
        'community_challenges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('goal_type', sa.String(50), nullable=False),  # individual, collective
        sa.Column('goal_value', sa.Float(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('max_participants', sa.Integer()),
        sa.Column('rewards', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_community_challenges_creator_id', 'community_challenges', ['creator_id'])
    op.create_index('idx_community_challenges_dates', 'community_challenges', ['start_date', 'end_date'])
    op.create_index('idx_community_challenges_is_public', 'community_challenges', ['is_public'])

    # Challenge participants table
    op.create_table(
        'challenge_participants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='active', nullable=False),  # active, completed, dropped
        sa.Column('progress', sa.Float(), default=0.0),
        sa.Column('progress_data', postgresql.JSONB(), default={}),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['challenge_id'], ['community_challenges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('challenge_id', 'user_id', name='uq_challenge_participant'),
    )
    op.create_index('idx_challenge_participants_challenge_id', 'challenge_participants', ['challenge_id'])
    op.create_index('idx_challenge_participants_user_id', 'challenge_participants', ['user_id'])
    op.create_index('idx_challenge_participants_status', 'challenge_participants', ['status'])


    # ==================== INTEGRATION TABLES ====================

    # User integrations table
    op.create_table(
        'user_integrations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # google_calendar, fitbit, oura, spotify, etc.
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('access_token', sa.Text()),
        sa.Column('refresh_token', sa.Text()),
        sa.Column('token_expires_at', sa.DateTime(timezone=True)),
        sa.Column('scopes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('provider_user_id', sa.String(200)),
        sa.Column('provider_metadata', postgresql.JSONB(), default={}),
        sa.Column('sync_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('sync_frequency', sa.String(20), default='hourly'),  # hourly, daily, weekly, manual
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('next_sync_at', sa.DateTime(timezone=True)),
        sa.Column('sync_status', sa.String(20), default='idle'),  # idle, syncing, error
        sa.Column('sync_error', sa.Text()),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_integration'),
    )
    op.create_index('idx_user_integrations_user_id', 'user_integrations', ['user_id'])
    op.create_index('idx_user_integrations_provider', 'user_integrations', ['provider'])
    op.create_index('idx_user_integrations_is_active', 'user_integrations', ['is_active'])
    op.create_index('idx_user_integrations_next_sync', 'user_integrations', ['next_sync_at'])

    # Synced data table
    op.create_table(
        'synced_data',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),  # calendar_event, sleep_session, activity, etc.
        sa.Column('external_id', sa.String(200), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(), nullable=False),
        sa.Column('processed', sa.Boolean(), default=False, nullable=False),
        sa.Column('life_event_id', postgresql.UUID(as_uuid=True)),
        sa.Column('data_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['integration_id'], ['user_integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['life_event_id'], ['events.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('integration_id', 'external_id', name='uq_synced_data'),
    )
    op.create_index('idx_synced_data_integration_id', 'synced_data', ['integration_id'])
    op.create_index('idx_synced_data_type', 'synced_data', ['data_type'])
    op.create_index('idx_synced_data_processed', 'synced_data', ['processed'])
    op.create_index('idx_synced_data_timestamp', 'synced_data', ['data_timestamp'])
    op.create_index('idx_synced_data_raw_gin', 'synced_data', ['raw_data'], postgresql_using='gin')


def downgrade():
    # Drop integration tables
    op.drop_table('synced_data')
    op.drop_table('user_integrations')

    # Drop social tables
    op.drop_table('challenge_participants')
    op.drop_table('community_challenges')
    op.drop_table('partnership_check_ins')
    op.drop_table('accountability_partnerships')
    op.drop_table('post_likes')
    op.drop_table('post_comments')
    op.drop_table('group_posts')
    op.drop_table('group_memberships')
    op.drop_table('groups')
    op.drop_table('friendships')

    # Drop gamification tables
    op.drop_table('leaderboards')
    op.drop_table('user_challenges')
    op.drop_table('daily_challenges')
    op.drop_table('streaks')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('user_achievements')
    op.drop_table('achievements')
    op.drop_table('user_levels')
