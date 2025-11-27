"""
Feast Data Sources

Defines data sources for feature views.
Data is pulled from PostgreSQL for offline store.
"""
from feast import FileSource, PushSource
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.data_format import ParquetFormat


# ==================== POSTGRESQL DATA SOURCES ====================

# User Activity Source
user_activity_source = PostgreSQLSource(
    name="user_activity_features_source",
    query="""
        SELECT
            user_id::text as user_id,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '24 hours') as activity_count_24h,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days') as activity_count_7d,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days') as activity_count_30d,
            COALESCE(SUM(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '24 hours'), 0)::float as total_minutes_24h,
            COALESCE(SUM(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 0)::float as total_minutes_7d,
            COALESCE(SUM(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days'), 0)::float as total_minutes_30d,
            COUNT(DISTINCT category) FILTER (WHERE start_time >= NOW() - INTERVAL '24 hours') as activity_diversity_24h,
            COUNT(DISTINCT category) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days') as activity_diversity_7d,
            COUNT(DISTINCT category) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days') as activity_diversity_30d,
            MODE() WITHIN GROUP (ORDER BY category) FILTER (WHERE start_time >= NOW() - INTERVAL '24 hours') as most_common_activity_24h,
            COALESCE(AVG(energy_level) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 7.0)::float as avg_energy_7d,
            COALESCE(AVG(mood_level) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 7.0)::float as avg_mood_7d,
            MAX(created_at) as event_timestamp
        FROM life_events
        WHERE user_id IS NOT NULL
        GROUP BY user_id
    """,
    timestamp_field="event_timestamp",
)


# Sleep Metrics Source
sleep_metrics_source = PostgreSQLSource(
    name="sleep_features_source",
    query="""
        SELECT
            user_id::text as user_id,
            COALESCE(AVG(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 480)::float as avg_sleep_duration_7d,
            COALESCE(AVG(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days'), 480)::float as avg_sleep_duration_30d,
            COALESCE(STDDEV(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 30)::float as sleep_consistency_7d,
            COALESCE(AVG(EXTRACT(HOUR FROM start_time)) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 22)::float as avg_bedtime_hour_7d,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days') as sleep_sessions_7d,
            GREATEST(0, (8 * 60) - COALESCE(AVG(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 480)) * 7 as sleep_debt_minutes,
            LEAST(1.0, COALESCE(AVG(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 480) / (8 * 60))::float as sleep_quality_score,
            COALESCE(AVG((metadata->>'deep_sleep_minutes')::float) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 90)::float as avg_deep_sleep_minutes_7d,
            COALESCE(AVG((metadata->>'rem_sleep_minutes')::float) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 120)::float as avg_rem_sleep_minutes_7d,
            MAX(created_at) as event_timestamp
        FROM life_events
        WHERE category = 'sleep'
        AND user_id IS NOT NULL
        GROUP BY user_id
    """,
    timestamp_field="event_timestamp",
)


# Exercise Metrics Source
exercise_metrics_source = PostgreSQLSource(
    name="exercise_features_source",
    query="""
        SELECT
            user_id::text as user_id,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days') as exercise_count_7d,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days') as exercise_count_30d,
            COALESCE(SUM(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 0)::float as exercise_minutes_7d,
            COALESCE(SUM(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '30 days'), 0)::float as exercise_minutes_30d,
            COALESCE(AVG(duration_minutes) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 30)::float as avg_exercise_duration_7d,
            COALESCE(AVG(energy_level) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 7.0)::float as avg_energy_after_exercise_7d,
            LEAST(1.0, COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days') / 5.0)::float as exercise_consistency_score,
            COALESCE(COUNT(DISTINCT tags) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days'), 1)::float / 5.0 as workout_variety_score_7d,
            COUNT(*) FILTER (WHERE start_time >= NOW() - INTERVAL '7 days' AND (metadata->>'intensity')::text = 'high') as high_intensity_count_7d,
            MAX(created_at) as event_timestamp
        FROM life_events
        WHERE category = 'exercise'
        AND user_id IS NOT NULL
        GROUP BY user_id
    """,
    timestamp_field="event_timestamp",
)


# Social Metrics Source
social_metrics_source = PostgreSQLSource(
    name="social_features_source",
    query="""
        SELECT
            u.id::text as user_id,
            COALESCE(f.friend_count, 0) as friend_count,
            COALESCE(p.posts_7d, 0) as posts_7d,
            COALESCE(c.comments_7d, 0) as comments_7d,
            COALESCE(l.likes_received_7d, 0) as likes_received_7d,
            COALESCE(lg.likes_given_7d, 0) as likes_given_7d,
            (
                LEAST(COALESCE(f.friend_count, 0) / 50.0, 1.0) * 0.4 +
                LEAST(COALESCE(p.posts_7d, 0) / 7.0, 1.0) * 0.3 +
                LEAST(COALESCE(c.comments_7d, 0) / 14.0, 1.0) * 0.2 +
                LEAST(COALESCE(l.likes_received_7d, 0) / 50.0, 1.0) * 0.1
            )::float as social_engagement_score,
            CASE WHEN COALESCE(p.posts_7d, 0) > 0
                THEN (COALESCE(l.likes_received_7d, 0)::float / p.posts_7d)
                ELSE 0
            END as avg_post_likes,
            CASE WHEN COALESCE(p.posts_7d, 0) > 0
                THEN (COALESCE(c.comments_7d, 0)::float / p.posts_7d)
                ELSE 0
            END as comment_rate_7d,
            COALESCE(fi.interactions_7d, 0) as friend_interactions_7d,
            GREATEST(
                u.updated_at,
                COALESCE(p.last_post, u.updated_at),
                COALESCE(c.last_comment, u.updated_at)
            ) as event_timestamp
        FROM users u
        LEFT JOIN (
            SELECT
                CASE WHEN user_id < friend_id THEN user_id ELSE friend_id END as uid,
                COUNT(*) as friend_count
            FROM friendships
            WHERE status = 'accepted'
            GROUP BY uid
        ) f ON f.uid = u.id
        LEFT JOIN (
            SELECT author_id, COUNT(*) as posts_7d, MAX(created_at) as last_post
            FROM posts
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY author_id
        ) p ON p.author_id = u.id
        LEFT JOIN (
            SELECT author_id, COUNT(*) as comments_7d, MAX(created_at) as last_comment
            FROM comments
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY author_id
        ) c ON c.author_id = u.id
        LEFT JOIN (
            SELECT p.author_id, COUNT(*) as likes_received_7d
            FROM post_likes pl
            INNER JOIN posts p ON p.id = pl.post_id
            WHERE pl.created_at >= NOW() - INTERVAL '7 days'
            GROUP BY p.author_id
        ) l ON l.author_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as likes_given_7d
            FROM post_likes
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY user_id
        ) lg ON lg.user_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as interactions_7d
            FROM (
                SELECT author_id as user_id FROM posts WHERE created_at >= NOW() - INTERVAL '7 days'
                UNION ALL
                SELECT author_id FROM comments WHERE created_at >= NOW() - INTERVAL '7 days'
                UNION ALL
                SELECT user_id FROM post_likes WHERE created_at >= NOW() - INTERVAL '7 days'
            ) interactions
            GROUP BY user_id
        ) fi ON fi.user_id = u.id
        WHERE u.is_active = true
    """,
    timestamp_field="event_timestamp",
)


# Integration Metrics Source
integration_metrics_source = PostgreSQLSource(
    name="integration_features_source",
    query="""
        SELECT
            user_id::text as user_id,
            COUNT(*) FILTER (WHERE status = 'connected') as active_integrations_count,
            COALESCE(
                EXTRACT(EPOCH FROM (NOW() - MAX(last_sync_at))) / 3600,
                999
            )::float as last_sync_hours_ago,
            COALESCE(
                AVG((id.value->>'heart_rate')::float) FILTER (
                    WHERE id.data_type = 'heart_rate'
                    AND id.recorded_at >= NOW() - INTERVAL '7 days'
                ),
                70
            )::float as avg_heart_rate_7d,
            COALESCE(
                AVG((id.value->>'steps')::int) FILTER (
                    WHERE id.data_type = 'steps'
                    AND id.recorded_at >= NOW() - INTERVAL '7 days'
                ),
                5000
            ) as avg_steps_7d,
            COALESCE(
                AVG((id.value->>'calories')::float) FILTER (
                    WHERE id.data_type = 'calories'
                    AND id.recorded_at >= NOW() - INTERVAL '7 days'
                ),
                2000
            )::float as avg_calories_7d,
            CASE
                WHEN COUNT(*) FILTER (WHERE status = 'connected') > 0
                THEN (
                    COUNT(*) FILTER (WHERE last_sync_at >= NOW() - INTERVAL '48 hours')::float /
                    COUNT(*) FILTER (WHERE status = 'connected')
                )
                ELSE 0
            END as data_completeness_score,
            CASE
                WHEN COUNT(*) FILTER (WHERE status = 'connected') > 0
                THEN (
                    COUNT(*) FILTER (WHERE status = 'connected' AND error_count < 3)::float /
                    COUNT(*) FILTER (WHERE status = 'connected')
                )
                ELSE 1
            END as sync_reliability_score,
            MAX(GREATEST(ui.updated_at, COALESCE(id.recorded_at, ui.updated_at))) as event_timestamp
        FROM user_integrations ui
        LEFT JOIN integration_data id ON id.user_id = ui.user_id AND id.provider = ui.provider
        WHERE ui.user_id IS NOT NULL
        GROUP BY ui.user_id
    """,
    timestamp_field="event_timestamp",
)


# ==================== PUSH SOURCES (For Real-time Updates) ====================

# Push source for real-time feature updates
user_activity_push_source = PushSource(
    name="user_activity_push",
    batch_source=user_activity_source,
)

sleep_metrics_push_source = PushSource(
    name="sleep_metrics_push",
    batch_source=sleep_metrics_source,
)

exercise_metrics_push_source = PushSource(
    name="exercise_metrics_push",
    batch_source=exercise_metrics_source,
)
