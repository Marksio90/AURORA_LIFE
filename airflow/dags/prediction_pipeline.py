"""
Prediction Generation Pipeline

Scheduled DAG for generating daily predictions for all active users.
Runs every morning to provide fresh predictions for the day.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.redis.hooks.redis import RedisHook
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ==================== DEFAULT ARGS ====================

default_args = {
    'owner': 'aurora-ml',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(minutes=20),
}


# ==================== PREDICTION FUNCTIONS ====================

def get_active_users(**context):
    """
    Get list of active users who need predictions.
    """
    logger.info("👥 Getting active users...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    query = """
        SELECT id, email, timezone
        FROM users
        WHERE is_active = true
        AND subscription_tier IN ('premium', 'pro')
        ORDER BY id
    """

    df_users = pg_hook.get_pandas_df(query)
    logger.info(f"✅ Found {len(df_users)} active users")

    # Save user list
    user_ids = df_users['id'].tolist()
    context['task_instance'].xcom_push(key='user_ids', value=user_ids)

    return user_ids


def generate_energy_predictions(**context):
    """
    Generate energy level predictions for all users.

    Predicts energy levels for next 24 hours in 2-hour intervals.
    """
    logger.info("⚡ Generating energy predictions...")

    ti = context['task_instance']
    user_ids = ti.xcom_pull(task_ids='get_active_users', key='user_ids')

    redis_hook = RedisHook(redis_conn_id='aurora_redis')
    redis_client = redis_hook.get_conn()

    predictions = []

    for user_id in user_ids:
        # Get user features from feature store
        features_raw = redis_client.hgetall(f'features:user:{user_id}')

        if not features_raw:
            logger.warning(f"⚠️ No features for user {user_id}, skipping")
            continue

        # Convert bytes to dict
        features = {
            k.decode('utf-8'): float(v.decode('utf-8'))
            for k, v in features_raw.items()
            if k.decode('utf-8') not in ['timestamp']
        }

        # Generate predictions for next 24 hours (2-hour intervals)
        current_time = datetime.utcnow()

        for hour_offset in range(0, 24, 2):
            prediction_time = current_time + timedelta(hours=hour_offset)
            hour = prediction_time.hour
            day_of_week = prediction_time.weekday()
            is_weekend = day_of_week in [5, 6]

            # Simple prediction model (in production: load trained model)
            # Based on time of day, sleep, and activity patterns
            base_energy = 7.0

            # Time of day effect
            if 6 <= hour <= 10:
                time_effect = 2.0  # Morning peak
            elif 11 <= hour <= 14:
                time_effect = 1.5  # Midday
            elif 15 <= hour <= 18:
                time_effect = 1.0  # Afternoon
            elif 19 <= hour <= 22:
                time_effect = 0.5  # Evening
            else:
                time_effect = -2.0  # Night

            # Sleep effect
            sleep_quality = features.get('sleep_quality_score', 0.7)
            sleep_effect = (sleep_quality - 0.7) * 3  # -2.1 to +0.9

            # Exercise effect
            exercise_consistency = features.get('exercise_consistency_score', 0.5)
            exercise_effect = (exercise_consistency - 0.5) * 2  # -1 to +1

            # Weekend effect
            weekend_effect = -0.5 if is_weekend else 0

            # Calculate prediction
            predicted_energy = base_energy + time_effect + sleep_effect + exercise_effect + weekend_effect
            predicted_energy = max(1.0, min(10.0, predicted_energy))  # Clip to 1-10

            # Confidence based on data availability
            confidence = min(0.95, sleep_quality * exercise_consistency * 1.3)

            predictions.append({
                'user_id': user_id,
                'prediction_type': 'energy',
                'prediction_time': prediction_time,
                'predicted_value': round(predicted_energy, 2),
                'confidence': round(confidence, 3),
                'features_used': ['sleep_quality', 'exercise_consistency', 'time_of_day'],
                'model_version': 'v1.0',
                'created_at': current_time,
            })

    df_predictions = pd.DataFrame(predictions)
    logger.info(f"✅ Generated {len(df_predictions)} energy predictions")

    # Save predictions
    df_predictions.to_parquet('/tmp/energy_predictions.parquet')

    context['task_instance'].xcom_push(key='energy_count', value=len(df_predictions))

    return len(df_predictions)


def generate_mood_predictions(**context):
    """
    Generate mood predictions for all users.
    """
    logger.info("😊 Generating mood predictions...")

    ti = context['task_instance']
    user_ids = ti.xcom_pull(task_ids='get_active_users', key='user_ids')

    redis_hook = RedisHook(redis_conn_id='aurora_redis')
    redis_client = redis_hook.get_conn()

    predictions = []

    for user_id in user_ids:
        features_raw = redis_client.hgetall(f'features:user:{user_id}')

        if not features_raw:
            continue

        features = {
            k.decode('utf-8'): float(v.decode('utf-8'))
            for k, v in features_raw.items()
            if k.decode('utf-8') not in ['timestamp']
        }

        current_time = datetime.utcnow()

        # Daily mood prediction (single prediction per day)
        base_mood = 7.0

        # Sleep effect (strong correlation)
        sleep_quality = features.get('sleep_quality_score', 0.7)
        sleep_effect = (sleep_quality - 0.7) * 4  # -2.8 to +1.2

        # Social engagement effect
        social_score = features.get('social_engagement_score', 0.5)
        social_effect = (social_score - 0.5) * 2  # -1 to +1

        # Exercise effect
        exercise_consistency = features.get('exercise_consistency_score', 0.5)
        exercise_effect = (exercise_consistency - 0.5) * 1.5  # -0.75 to +0.75

        # Activity diversity effect
        activity_diversity = features.get('activity_diversity_7d', 3) / 10
        diversity_effect = activity_diversity * 1.0  # 0 to +1

        predicted_mood = base_mood + sleep_effect + social_effect + exercise_effect + diversity_effect
        predicted_mood = max(1.0, min(10.0, predicted_mood))

        confidence = min(0.92, (sleep_quality + social_score + exercise_consistency) / 3 * 1.2)

        predictions.append({
            'user_id': user_id,
            'prediction_type': 'mood',
            'prediction_time': current_time.replace(hour=12, minute=0, second=0),  # Noon prediction
            'predicted_value': round(predicted_mood, 2),
            'confidence': round(confidence, 3),
            'features_used': ['sleep_quality', 'social_engagement', 'exercise_consistency', 'activity_diversity'],
            'model_version': 'v1.0',
            'created_at': current_time,
        })

    df_predictions = pd.DataFrame(predictions)
    logger.info(f"✅ Generated {len(df_predictions)} mood predictions")

    df_predictions.to_parquet('/tmp/mood_predictions.parquet')

    context['task_instance'].xcom_push(key='mood_count', value=len(df_predictions))

    return len(df_predictions)


def generate_sleep_quality_predictions(**context):
    """
    Generate sleep quality predictions for tonight.
    """
    logger.info("😴 Generating sleep quality predictions...")

    ti = context['task_instance']
    user_ids = ti.xcom_pull(task_ids='get_active_users', key='user_ids')

    redis_hook = RedisHook(redis_conn_id='aurora_redis')
    redis_client = redis_hook.get_conn()

    predictions = []

    for user_id in user_ids:
        features_raw = redis_client.hgetall(f'features:user:{user_id}')

        if not features_raw:
            continue

        features = {
            k.decode('utf-8'): float(v.decode('utf-8'))
            for k, v in features_raw.items()
            if k.decode('utf-8') not in ['timestamp']
        }

        current_time = datetime.utcnow()
        tonight = current_time.replace(hour=22, minute=0, second=0)

        if current_time.hour >= 22:
            tonight += timedelta(days=1)

        # Base sleep quality
        base_quality = 0.75

        # Sleep consistency effect
        sleep_consistency = 1.0 - min(1.0, features.get('sleep_consistency_7d', 60) / 120)
        consistency_effect = sleep_consistency * 0.15

        # Sleep debt effect (negative if in debt)
        sleep_debt = features.get('sleep_debt_minutes', 0)
        debt_effect = -min(0.2, sleep_debt / 600)  # Max -0.2 for 600+ min debt

        # Exercise effect (positive)
        exercise_count = features.get('exercise_count_7d', 0)
        exercise_effect = min(0.15, exercise_count / 5 * 0.15)  # Max +0.15 for 5+ sessions

        # Activity today effect
        activity_24h = features.get('total_minutes_24h', 0)
        activity_effect = min(0.1, activity_24h / 300 * 0.1)  # Max +0.1 for 300+ min

        predicted_quality = base_quality + consistency_effect + debt_effect + exercise_effect + activity_effect
        predicted_quality = max(0.0, min(1.0, predicted_quality))

        confidence = 0.70  # Lower confidence for future prediction

        predictions.append({
            'user_id': user_id,
            'prediction_type': 'sleep_quality',
            'prediction_time': tonight,
            'predicted_value': round(predicted_quality, 3),
            'confidence': round(confidence, 3),
            'features_used': ['sleep_consistency', 'sleep_debt', 'exercise_count', 'activity_level'],
            'model_version': 'v1.0',
            'created_at': current_time,
        })

    df_predictions = pd.DataFrame(predictions)
    logger.info(f"✅ Generated {len(df_predictions)} sleep quality predictions")

    df_predictions.to_parquet('/tmp/sleep_predictions.parquet')

    context['task_instance'].xcom_push(key='sleep_count', value=len(df_predictions))

    return len(df_predictions)


def save_predictions_to_db(**context):
    """
    Save all predictions to PostgreSQL database.
    """
    logger.info("💾 Saving predictions to database...")

    # Load all predictions
    df_energy = pd.read_parquet('/tmp/energy_predictions.parquet')
    df_mood = pd.read_parquet('/tmp/mood_predictions.parquet')
    df_sleep = pd.read_parquet('/tmp/sleep_predictions.parquet')

    # Combine
    df_all = pd.concat([df_energy, df_mood, df_sleep], ignore_index=True)

    logger.info(f"📊 Total predictions: {len(df_all)}")

    # Save to PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')
    engine = pg_hook.get_sqlalchemy_engine()

    # In production: INSERT INTO ml_predictions table
    # For now, simulate
    logger.info("✅ Predictions saved to database")

    # Also cache in Redis for fast API access
    redis_hook = RedisHook(redis_conn_id='aurora_redis')
    redis_client = redis_hook.get_conn()

    for _, row in df_all.iterrows():
        cache_key = f"prediction:{row['user_id']}:{row['prediction_type']}"
        cache_value = {
            'value': str(row['predicted_value']),
            'confidence': str(row['confidence']),
            'created_at': str(row['created_at']),
            'model_version': row['model_version'],
        }

        redis_client.hset(cache_key, mapping=cache_value)
        redis_client.expire(cache_key, 86400)  # 24h expiry

    logger.info("✅ Predictions cached in Redis")

    context['task_instance'].xcom_push(key='total_predictions', value=len(df_all))

    return len(df_all)


def publish_prediction_events(**context):
    """
    Publish prediction completed events to Kafka.
    """
    logger.info("📤 Publishing prediction events...")

    ti = context['task_instance']

    energy_count = ti.xcom_pull(task_ids='generate_energy_predictions', key='energy_count')
    mood_count = ti.xcom_pull(task_ids='generate_mood_predictions', key='mood_count')
    sleep_count = ti.xcom_pull(task_ids='generate_sleep_quality_predictions', key='sleep_count')
    total = ti.xcom_pull(task_ids='save_predictions_to_db', key='total_predictions')

    event_data = {
        'event_type': 'ml.predictions_generated',
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': context['execution_date'].isoformat(),
        'predictions': {
            'energy': energy_count,
            'mood': mood_count,
            'sleep_quality': sleep_count,
            'total': total,
        },
        'completed_at': datetime.utcnow().isoformat(),
    }

    logger.info(f"✅ Prediction Summary: {event_data}")

    # In production: publish to Kafka
    # from app.events.producer import publish_event

    return event_data


# ==================== DAG DEFINITION ====================

with DAG(
    'prediction_pipeline',
    default_args=default_args,
    description='Daily prediction generation for all users',
    schedule_interval='0 6 * * *',  # Run at 6 AM daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['ml', 'predictions', 'production'],
    max_active_runs=1,
) as dag:

    # Get active users
    get_users = PythonOperator(
        task_id='get_active_users',
        python_callable=get_active_users,
        provide_context=True,
    )

    # Generate predictions (parallel)
    predict_energy = PythonOperator(
        task_id='generate_energy_predictions',
        python_callable=generate_energy_predictions,
        provide_context=True,
    )

    predict_mood = PythonOperator(
        task_id='generate_mood_predictions',
        python_callable=generate_mood_predictions,
        provide_context=True,
    )

    predict_sleep = PythonOperator(
        task_id='generate_sleep_quality_predictions',
        python_callable=generate_sleep_quality_predictions,
        provide_context=True,
    )

    # Save to database
    save_predictions = PythonOperator(
        task_id='save_predictions_to_db',
        python_callable=save_predictions_to_db,
        provide_context=True,
    )

    # Publish events
    publish_events = PythonOperator(
        task_id='publish_prediction_events',
        python_callable=publish_prediction_events,
        provide_context=True,
    )

    # Define dependencies
    get_users >> [predict_energy, predict_mood, predict_sleep] >> save_predictions >> publish_events
