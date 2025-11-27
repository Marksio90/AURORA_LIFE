"""
Feature Engineering Pipeline

Scheduled DAG for computing and updating features in the Feature Store.
Runs every 6 hours to keep features fresh for real-time predictions.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ==================== DEFAULT ARGS ====================

default_args = {
    'owner': 'aurora-ml',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=3),
    'execution_timeout': timedelta(minutes=30),
}


# ==================== FEATURE COMPUTATION ====================

def compute_user_activity_features(**context):
    """
    Compute user activity features (last 24h, 7d, 30d aggregations).

    Features:
    - Total activity minutes (24h, 7d, 30d)
    - Activity diversity score
    - Most common activity
    - Activity streak
    """
    logger.info("🔧 Computing user activity features...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    # Get all active users
    users_query = "SELECT id FROM users WHERE is_active = true"
    df_users = pg_hook.get_pandas_df(users_query)

    features = []

    for user_id in df_users['id']:
        # Activity in last 24h
        query_24h = f"""
            SELECT
                COUNT(*) as activity_count_24h,
                SUM(duration_minutes) as total_minutes_24h,
                COUNT(DISTINCT category) as activity_diversity_24h,
                MODE() WITHIN GROUP (ORDER BY category) as most_common_activity_24h
            FROM life_events
            WHERE user_id = '{user_id}'
            AND start_time >= NOW() - INTERVAL '24 hours'
        """
        df_24h = pg_hook.get_pandas_df(query_24h)

        # Activity in last 7 days
        query_7d = f"""
            SELECT
                COUNT(*) as activity_count_7d,
                SUM(duration_minutes) as total_minutes_7d,
                COUNT(DISTINCT category) as activity_diversity_7d,
                AVG(energy_level) as avg_energy_7d,
                AVG(mood_level) as avg_mood_7d
            FROM life_events
            WHERE user_id = '{user_id}'
            AND start_time >= NOW() - INTERVAL '7 days'
        """
        df_7d = pg_hook.get_pandas_df(query_7d)

        # Activity in last 30 days
        query_30d = f"""
            SELECT
                COUNT(*) as activity_count_30d,
                SUM(duration_minutes) as total_minutes_30d,
                COUNT(DISTINCT category) as activity_diversity_30d
            FROM life_events
            WHERE user_id = '{user_id}'
            AND start_time >= NOW() - INTERVAL '30 days'
        """
        df_30d = pg_hook.get_pandas_df(query_30d)

        # Combine features
        user_features = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            **df_24h.iloc[0].to_dict(),
            **df_7d.iloc[0].to_dict(),
            **df_30d.iloc[0].to_dict(),
        }

        features.append(user_features)

    df_features = pd.DataFrame(features)
    logger.info(f"✅ Computed activity features for {len(df_features)} users")

    # Save to feature store (in production: Feast)
    df_features.to_parquet('/tmp/activity_features.parquet')

    return len(df_features)


def compute_sleep_features(**context):
    """
    Compute sleep-related features.

    Features:
    - Average sleep duration (7d, 30d)
    - Sleep consistency score
    - Average bedtime
    - Sleep debt
    """
    logger.info("🔧 Computing sleep features...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    users_query = "SELECT id FROM users WHERE is_active = true"
    df_users = pg_hook.get_pandas_df(users_query)

    features = []

    for user_id in df_users['id']:
        # Sleep data
        query = f"""
            SELECT
                AVG(duration_minutes) as avg_sleep_duration_7d,
                STDDEV(duration_minutes) as sleep_consistency_7d,
                AVG(EXTRACT(HOUR FROM start_time)) as avg_bedtime_hour_7d,
                COUNT(*) as sleep_sessions_7d
            FROM life_events
            WHERE user_id = '{user_id}'
            AND category = 'sleep'
            AND start_time >= NOW() - INTERVAL '7 days'
        """
        df_sleep = pg_hook.get_pandas_df(query)

        # Calculate sleep debt (optimal 8h)
        avg_sleep = df_sleep.iloc[0]['avg_sleep_duration_7d'] or 0
        sleep_debt = max(0, (8 * 60) - avg_sleep) * 7  # Total debt in minutes

        user_features = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            **df_sleep.iloc[0].to_dict(),
            'sleep_debt_minutes': sleep_debt,
            'sleep_quality_score': min(1.0, avg_sleep / (8 * 60)) if avg_sleep > 0 else 0,
        }

        features.append(user_features)

    df_features = pd.DataFrame(features)
    logger.info(f"✅ Computed sleep features for {len(df_features)} users")

    df_features.to_parquet('/tmp/sleep_features.parquet')

    return len(df_features)


def compute_exercise_features(**context):
    """
    Compute exercise-related features.

    Features:
    - Exercise frequency (7d, 30d)
    - Total exercise minutes
    - Exercise variety score
    - Workout intensity trend
    """
    logger.info("🔧 Computing exercise features...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    users_query = "SELECT id FROM users WHERE is_active = true"
    df_users = pg_hook.get_pandas_df(users_query)

    features = []

    for user_id in df_users['id']:
        query_7d = f"""
            SELECT
                COUNT(*) as exercise_count_7d,
                SUM(duration_minutes) as exercise_minutes_7d,
                AVG(duration_minutes) as avg_exercise_duration_7d,
                AVG(energy_level) as avg_energy_after_exercise_7d
            FROM life_events
            WHERE user_id = '{user_id}'
            AND category = 'exercise'
            AND start_time >= NOW() - INTERVAL '7 days'
        """
        df_7d = pg_hook.get_pandas_df(query_7d)

        query_30d = f"""
            SELECT
                COUNT(*) as exercise_count_30d,
                SUM(duration_minutes) as exercise_minutes_30d
            FROM life_events
            WHERE user_id = '{user_id}'
            AND category = 'exercise'
            AND start_time >= NOW() - INTERVAL '30 days'
        """
        df_30d = pg_hook.get_pandas_df(query_30d)

        # Exercise consistency (sessions per week)
        exercise_frequency = df_7d.iloc[0]['exercise_count_7d'] or 0

        user_features = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            **df_7d.iloc[0].to_dict(),
            **df_30d.iloc[0].to_dict(),
            'exercise_consistency_score': min(1.0, exercise_frequency / 5),  # 5 sessions/week = 1.0
        }

        features.append(user_features)

    df_features = pd.DataFrame(features)
    logger.info(f"✅ Computed exercise features for {len(df_features)} users")

    df_features.to_parquet('/tmp/exercise_features.parquet')

    return len(df_features)


def compute_social_features(**context):
    """
    Compute social engagement features.

    Features:
    - Friend count
    - Post frequency
    - Engagement rate
    - Social activity score
    """
    logger.info("🔧 Computing social features...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    users_query = "SELECT id FROM users WHERE is_active = true"
    df_users = pg_hook.get_pandas_df(users_query)

    features = []

    for user_id in df_users['id']:
        # Friend count
        friends_query = f"""
            SELECT COUNT(*) as friend_count
            FROM friendships
            WHERE (user_id = '{user_id}' OR friend_id = '{user_id}')
            AND status = 'accepted'
        """
        df_friends = pg_hook.get_pandas_df(friends_query)

        # Social activity (last 7 days)
        social_query = f"""
            SELECT
                COUNT(DISTINCT p.id) as posts_7d,
                COUNT(DISTINCT c.id) as comments_7d,
                COUNT(DISTINCT l.id) as likes_received_7d
            FROM users u
            LEFT JOIN posts p ON p.author_id = u.id
                AND p.created_at >= NOW() - INTERVAL '7 days'
            LEFT JOIN comments c ON c.author_id = u.id
                AND c.created_at >= NOW() - INTERVAL '7 days'
            LEFT JOIN post_likes l ON l.post_id IN (
                SELECT id FROM posts WHERE author_id = u.id
            ) AND l.created_at >= NOW() - INTERVAL '7 days'
            WHERE u.id = '{user_id}'
            GROUP BY u.id
        """
        df_social = pg_hook.get_pandas_df(social_query)

        # Calculate social engagement score
        friend_count = df_friends.iloc[0]['friend_count'] or 0
        posts = df_social.iloc[0]['posts_7d'] or 0
        comments = df_social.iloc[0]['comments_7d'] or 0
        likes = df_social.iloc[0]['likes_received_7d'] or 0

        engagement_score = (
            min(friend_count / 50, 1.0) * 0.4 +  # Up to 50 friends
            min(posts / 7, 1.0) * 0.3 +          # Daily posts
            min(comments / 14, 1.0) * 0.2 +      # 2 comments/day
            min(likes / 50, 1.0) * 0.1           # Engagement
        )

        user_features = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'friend_count': friend_count,
            **df_social.iloc[0].to_dict(),
            'social_engagement_score': engagement_score,
        }

        features.append(user_features)

    df_features = pd.DataFrame(features)
    logger.info(f"✅ Computed social features for {len(df_features)} users")

    df_features.to_parquet('/tmp/social_features.parquet')

    return len(df_features)


def update_feature_store(**context):
    """
    Update feature store with computed features.

    In production, this would update Feast feature store.
    For now, we store in Redis for fast access.
    """
    logger.info("💾 Updating feature store...")

    from airflow.providers.redis.hooks.redis import RedisHook

    redis_hook = RedisHook(redis_conn_id='aurora_redis')
    redis_client = redis_hook.get_conn()

    # Load all computed features
    df_activity = pd.read_parquet('/tmp/activity_features.parquet')
    df_sleep = pd.read_parquet('/tmp/sleep_features.parquet')
    df_exercise = pd.read_parquet('/tmp/exercise_features.parquet')
    df_social = pd.read_parquet('/tmp/social_features.parquet')

    # Merge features
    df_features = df_activity.merge(df_sleep, on='user_id', how='outer', suffixes=('', '_sleep'))
    df_features = df_features.merge(df_exercise, on='user_id', how='outer', suffixes=('', '_exercise'))
    df_features = df_features.merge(df_social, on='user_id', how='outer', suffixes=('', '_social'))

    # Store in Redis (feature store simulation)
    features_stored = 0

    for _, row in df_features.iterrows():
        user_id = row['user_id']
        features_dict = row.to_dict()

        # Remove user_id and convert to strings
        features_dict.pop('user_id', None)
        features_dict = {k: str(v) for k, v in features_dict.items() if pd.notna(v)}

        # Store in Redis hash
        redis_client.hset(f'features:user:{user_id}', mapping=features_dict)

        # Set expiry (24 hours)
        redis_client.expire(f'features:user:{user_id}', 86400)

        features_stored += 1

    logger.info(f"✅ Updated feature store for {features_stored} users")

    # Store metadata
    redis_client.hset('features:metadata', mapping={
        'last_update': datetime.utcnow().isoformat(),
        'users_count': features_stored,
        'features_count': len(df_features.columns),
        'dag_run_id': context['dag_run'].run_id,
    })

    context['task_instance'].xcom_push(key='users_updated', value=features_stored)

    return features_stored


# ==================== DAG DEFINITION ====================

with DAG(
    'feature_engineering_pipeline',
    default_args=default_args,
    description='Feature engineering and feature store updates',
    schedule_interval='0 */6 * * *',  # Run every 6 hours
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['ml', 'features', 'production'],
    max_active_runs=1,
) as dag:

    # Parallel feature computation
    compute_activity = PythonOperator(
        task_id='compute_activity_features',
        python_callable=compute_user_activity_features,
        provide_context=True,
    )

    compute_sleep = PythonOperator(
        task_id='compute_sleep_features',
        python_callable=compute_sleep_features,
        provide_context=True,
    )

    compute_exercise = PythonOperator(
        task_id='compute_exercise_features',
        python_callable=compute_exercise_features,
        provide_context=True,
    )

    compute_social = PythonOperator(
        task_id='compute_social_features',
        python_callable=compute_social_features,
        provide_context=True,
    )

    # Update feature store
    update_store = PythonOperator(
        task_id='update_feature_store',
        python_callable=update_feature_store,
        provide_context=True,
    )

    # Define task dependencies (parallel computation, then update)
    [compute_activity, compute_sleep, compute_exercise, compute_social] >> update_store
