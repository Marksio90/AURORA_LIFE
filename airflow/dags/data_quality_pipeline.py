"""
Data Quality Monitoring Pipeline

Scheduled DAG for monitoring data quality across all data sources.
Validates data integrity, completeness, and correctness.
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
    'owner': 'aurora-data',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=15),
}


# ==================== DATA QUALITY CHECKS ====================

def check_life_events_quality(**context):
    """
    Validate life events data quality.

    Checks:
    - No duplicate events
    - Valid timestamps
    - Duration > 0
    - Valid energy/mood levels (1-10)
    - Required fields present
    """
    logger.info("🔍 Checking life events data quality...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    issues = []

    # Check 1: Duplicate events
    query_duplicates = """
        SELECT user_id, start_time, category, COUNT(*) as count
        FROM life_events
        WHERE start_time >= NOW() - INTERVAL '7 days'
        GROUP BY user_id, start_time, category
        HAVING COUNT(*) > 1
    """
    df_duplicates = pg_hook.get_pandas_df(query_duplicates)

    if len(df_duplicates) > 0:
        issues.append({
            'check': 'duplicates',
            'severity': 'warning',
            'count': len(df_duplicates),
            'message': f'Found {len(df_duplicates)} duplicate life events'
        })
        logger.warning(f"⚠️ Found {len(df_duplicates)} duplicate life events")

    # Check 2: Invalid durations
    query_invalid_duration = """
        SELECT COUNT(*) as count
        FROM life_events
        WHERE (duration_minutes <= 0 OR duration_minutes > 1440)
        AND start_time >= NOW() - INTERVAL '7 days'
    """
    df_invalid_duration = pg_hook.get_pandas_df(query_invalid_duration)
    invalid_duration_count = df_invalid_duration.iloc[0]['count']

    if invalid_duration_count > 0:
        issues.append({
            'check': 'invalid_duration',
            'severity': 'error',
            'count': invalid_duration_count,
            'message': f'{invalid_duration_count} events with invalid duration (≤0 or >24h)'
        })
        logger.error(f"❌ {invalid_duration_count} events with invalid duration")

    # Check 3: Invalid energy levels
    query_invalid_energy = """
        SELECT COUNT(*) as count
        FROM life_events
        WHERE (energy_level < 1 OR energy_level > 10)
        AND energy_level IS NOT NULL
        AND start_time >= NOW() - INTERVAL '7 days'
    """
    df_invalid_energy = pg_hook.get_pandas_df(query_invalid_energy)
    invalid_energy_count = df_invalid_energy.iloc[0]['count']

    if invalid_energy_count > 0:
        issues.append({
            'check': 'invalid_energy',
            'severity': 'error',
            'count': invalid_energy_count,
            'message': f'{invalid_energy_count} events with invalid energy level (not 1-10)'
        })
        logger.error(f"❌ {invalid_energy_count} events with invalid energy level")

    # Check 4: Invalid mood levels
    query_invalid_mood = """
        SELECT COUNT(*) as count
        FROM life_events
        WHERE (mood_level < 1 OR mood_level > 10)
        AND mood_level IS NOT NULL
        AND start_time >= NOW() - INTERVAL '7 days'
    """
    df_invalid_mood = pg_hook.get_pandas_df(query_invalid_mood)
    invalid_mood_count = df_invalid_mood.iloc[0]['count']

    if invalid_mood_count > 0:
        issues.append({
            'check': 'invalid_mood',
            'severity': 'error',
            'count': invalid_mood_count,
            'message': f'{invalid_mood_count} events with invalid mood level (not 1-10)'
        })
        logger.error(f"❌ {invalid_mood_count} events with invalid mood level")

    # Check 5: Future timestamps
    query_future = """
        SELECT COUNT(*) as count
        FROM life_events
        WHERE start_time > NOW()
    """
    df_future = pg_hook.get_pandas_df(query_future)
    future_count = df_future.iloc[0]['count']

    if future_count > 0:
        issues.append({
            'check': 'future_timestamp',
            'severity': 'warning',
            'count': future_count,
            'message': f'{future_count} events with future timestamps'
        })
        logger.warning(f"⚠️ {future_count} events with future timestamps")

    # Check 6: Missing required fields
    query_missing = """
        SELECT COUNT(*) as count
        FROM life_events
        WHERE user_id IS NULL
        OR category IS NULL
        OR start_time IS NULL
        AND created_at >= NOW() - INTERVAL '7 days'
    """
    df_missing = pg_hook.get_pandas_df(query_missing)
    missing_count = df_missing.iloc[0]['count']

    if missing_count > 0:
        issues.append({
            'check': 'missing_required_fields',
            'severity': 'critical',
            'count': missing_count,
            'message': f'{missing_count} events with missing required fields'
        })
        logger.critical(f"🚨 {missing_count} events with missing required fields")

    # Summary
    total_issues = sum(issue['count'] for issue in issues)

    if total_issues == 0:
        logger.info("✅ Life events data quality: PASSED")
    else:
        logger.warning(f"⚠️ Life events data quality: {total_issues} issues found")

    context['task_instance'].xcom_push(key='life_events_issues', value=issues)

    return issues


def check_users_quality(**context):
    """
    Validate users data quality.

    Checks:
    - Valid email formats
    - No duplicate emails
    - Valid subscription tiers
    - Active status consistency
    """
    logger.info("🔍 Checking users data quality...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    issues = []

    # Check 1: Invalid email format
    query_invalid_email = """
        SELECT COUNT(*) as count
        FROM users
        WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
    """
    df_invalid_email = pg_hook.get_pandas_df(query_invalid_email)
    invalid_email_count = df_invalid_email.iloc[0]['count']

    if invalid_email_count > 0:
        issues.append({
            'check': 'invalid_email',
            'severity': 'critical',
            'count': invalid_email_count,
            'message': f'{invalid_email_count} users with invalid email format'
        })
        logger.critical(f"🚨 {invalid_email_count} users with invalid email")

    # Check 2: Duplicate emails
    query_duplicate_email = """
        SELECT email, COUNT(*) as count
        FROM users
        GROUP BY email
        HAVING COUNT(*) > 1
    """
    df_duplicate_email = pg_hook.get_pandas_df(query_duplicate_email)

    if len(df_duplicate_email) > 0:
        issues.append({
            'check': 'duplicate_email',
            'severity': 'critical',
            'count': len(df_duplicate_email),
            'message': f'{len(df_duplicate_email)} duplicate email addresses'
        })
        logger.critical(f"🚨 {len(df_duplicate_email)} duplicate emails")

    # Check 3: Invalid subscription tier
    query_invalid_tier = """
        SELECT COUNT(*) as count
        FROM users
        WHERE subscription_tier NOT IN ('free', 'premium', 'pro')
    """
    df_invalid_tier = pg_hook.get_pandas_df(query_invalid_tier)
    invalid_tier_count = df_invalid_tier.iloc[0]['count']

    if invalid_tier_count > 0:
        issues.append({
            'check': 'invalid_subscription_tier',
            'severity': 'error',
            'count': invalid_tier_count,
            'message': f'{invalid_tier_count} users with invalid subscription tier'
        })
        logger.error(f"❌ {invalid_tier_count} users with invalid tier")

    # Check 4: Inactive users with recent activity
    query_inactive_active = """
        SELECT COUNT(DISTINCT u.id) as count
        FROM users u
        INNER JOIN life_events le ON le.user_id = u.id
        WHERE u.is_active = false
        AND le.created_at >= NOW() - INTERVAL '7 days'
    """
    df_inactive_active = pg_hook.get_pandas_df(query_inactive_active)
    inactive_active_count = df_inactive_active.iloc[0]['count']

    if inactive_active_count > 0:
        issues.append({
            'check': 'inactive_with_activity',
            'severity': 'warning',
            'count': inactive_active_count,
            'message': f'{inactive_active_count} inactive users with recent activity'
        })
        logger.warning(f"⚠️ {inactive_active_count} inactive users with activity")

    total_issues = sum(issue['count'] for issue in issues)

    if total_issues == 0:
        logger.info("✅ Users data quality: PASSED")
    else:
        logger.warning(f"⚠️ Users data quality: {total_issues} issues found")

    context['task_instance'].xcom_push(key='users_issues', value=issues)

    return issues


def check_integrations_quality(**context):
    """
    Validate integrations data quality.

    Checks:
    - Data freshness (last sync time)
    - Valid provider names
    - Sync success rate
    - Data completeness
    """
    logger.info("🔍 Checking integrations data quality...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    issues = []

    # Check 1: Stale integrations (no sync in 48h)
    query_stale = """
        SELECT COUNT(*) as count
        FROM user_integrations
        WHERE status = 'connected'
        AND last_sync_at < NOW() - INTERVAL '48 hours'
    """
    df_stale = pg_hook.get_pandas_df(query_stale)
    stale_count = df_stale.iloc[0]['count']

    if stale_count > 0:
        issues.append({
            'check': 'stale_integrations',
            'severity': 'warning',
            'count': stale_count,
            'message': f'{stale_count} integrations not synced in 48h'
        })
        logger.warning(f"⚠️ {stale_count} stale integrations")

    # Check 2: Invalid provider
    query_invalid_provider = """
        SELECT COUNT(*) as count
        FROM user_integrations
        WHERE provider NOT IN ('fitbit', 'oura', 'google_fit', 'apple_health', 'spotify', 'google_calendar')
    """
    df_invalid_provider = pg_hook.get_pandas_df(query_invalid_provider)
    invalid_provider_count = df_invalid_provider.iloc[0]['count']

    if invalid_provider_count > 0:
        issues.append({
            'check': 'invalid_provider',
            'severity': 'error',
            'count': invalid_provider_count,
            'message': f'{invalid_provider_count} integrations with invalid provider'
        })
        logger.error(f"❌ {invalid_provider_count} invalid providers")

    # Check 3: Failed integrations
    query_failed = """
        SELECT COUNT(*) as count
        FROM user_integrations
        WHERE status = 'error'
    """
    df_failed = pg_hook.get_pandas_df(query_failed)
    failed_count = df_failed.iloc[0]['count']

    if failed_count > 10:  # Threshold: 10 failed integrations
        issues.append({
            'check': 'many_failed_integrations',
            'severity': 'warning',
            'count': failed_count,
            'message': f'{failed_count} integrations in error state'
        })
        logger.warning(f"⚠️ {failed_count} failed integrations")

    # Check 4: Empty integration data
    query_empty = """
        SELECT ui.id, ui.provider
        FROM user_integrations ui
        LEFT JOIN integration_data id ON id.user_id = ui.user_id
            AND id.provider = ui.provider
        WHERE ui.status = 'connected'
        AND ui.last_sync_at IS NOT NULL
        AND id.id IS NULL
    """
    df_empty = pg_hook.get_pandas_df(query_empty)

    if len(df_empty) > 0:
        issues.append({
            'check': 'empty_integration_data',
            'severity': 'warning',
            'count': len(df_empty),
            'message': f'{len(df_empty)} connected integrations with no data'
        })
        logger.warning(f"⚠️ {len(df_empty)} integrations with no data")

    total_issues = sum(issue['count'] for issue in issues)

    if total_issues == 0:
        logger.info("✅ Integrations data quality: PASSED")
    else:
        logger.warning(f"⚠️ Integrations data quality: {total_issues} issues found")

    context['task_instance'].xcom_push(key='integrations_issues', value=issues)

    return issues


def check_gamification_quality(**context):
    """
    Validate gamification data quality.

    Checks:
    - XP totals consistency
    - Level calculations
    - Achievement unlocks validity
    - Streak calculations
    """
    logger.info("🔍 Checking gamification data quality...")

    pg_hook = PostgresHook(postgres_conn_id='aurora_postgres')

    issues = []

    # Check 1: Negative XP
    query_negative_xp = """
        SELECT COUNT(*) as count
        FROM user_profiles
        WHERE total_xp < 0
    """
    df_negative_xp = pg_hook.get_pandas_df(query_negative_xp)
    negative_xp_count = df_negative_xp.iloc[0]['count']

    if negative_xp_count > 0:
        issues.append({
            'check': 'negative_xp',
            'severity': 'critical',
            'count': negative_xp_count,
            'message': f'{negative_xp_count} users with negative XP'
        })
        logger.critical(f"🚨 {negative_xp_count} users with negative XP")

    # Check 2: Level-XP mismatch
    query_level_mismatch = """
        SELECT COUNT(*) as count
        FROM user_profiles
        WHERE level != FLOOR(POW(total_xp / 100, 0.5)) + 1
        AND total_xp > 0
    """
    df_level_mismatch = pg_hook.get_pandas_df(query_level_mismatch)
    level_mismatch_count = df_level_mismatch.iloc[0]['count']

    if level_mismatch_count > 0:
        issues.append({
            'check': 'level_xp_mismatch',
            'severity': 'error',
            'count': level_mismatch_count,
            'message': f'{level_mismatch_count} users with incorrect level calculation'
        })
        logger.error(f"❌ {level_mismatch_count} users with level-XP mismatch")

    # Check 3: Future achievement unlocks
    query_future_achievements = """
        SELECT COUNT(*) as count
        FROM user_achievements
        WHERE unlocked_at > NOW()
    """
    df_future = pg_hook.get_pandas_df(query_future_achievements)
    future_count = df_future.iloc[0]['count']

    if future_count > 0:
        issues.append({
            'check': 'future_achievements',
            'severity': 'error',
            'count': future_count,
            'message': f'{future_count} achievements unlocked in the future'
        })
        logger.error(f"❌ {future_count} future achievement unlocks")

    # Check 4: Orphaned achievements (no corresponding user)
    query_orphaned = """
        SELECT COUNT(*) as count
        FROM user_achievements ua
        LEFT JOIN users u ON u.id = ua.user_id
        WHERE u.id IS NULL
    """
    df_orphaned = pg_hook.get_pandas_df(query_orphaned)
    orphaned_count = df_orphaned.iloc[0]['count']

    if orphaned_count > 0:
        issues.append({
            'check': 'orphaned_achievements',
            'severity': 'error',
            'count': orphaned_count,
            'message': f'{orphaned_count} achievements without valid user'
        })
        logger.error(f"❌ {orphaned_count} orphaned achievements")

    total_issues = sum(issue['count'] for issue in issues)

    if total_issues == 0:
        logger.info("✅ Gamification data quality: PASSED")
    else:
        logger.warning(f"⚠️ Gamification data quality: {total_issues} issues found")

    context['task_instance'].xcom_push(key='gamification_issues', value=issues)

    return issues


def generate_quality_report(**context):
    """
    Generate comprehensive data quality report.
    """
    logger.info("📊 Generating data quality report...")

    ti = context['task_instance']

    # Collect all issues
    life_events_issues = ti.xcom_pull(task_ids='check_life_events_quality', key='life_events_issues') or []
    users_issues = ti.xcom_pull(task_ids='check_users_quality', key='users_issues') or []
    integrations_issues = ti.xcom_pull(task_ids='check_integrations_quality', key='integrations_issues') or []
    gamification_issues = ti.xcom_pull(task_ids='check_gamification_quality', key='gamification_issues') or []

    # Count by severity
    critical_count = sum(
        1 for issues in [life_events_issues, users_issues, integrations_issues, gamification_issues]
        for issue in issues if issue.get('severity') == 'critical'
    )

    error_count = sum(
        1 for issues in [life_events_issues, users_issues, integrations_issues, gamification_issues]
        for issue in issues if issue.get('severity') == 'error'
    )

    warning_count = sum(
        1 for issues in [life_events_issues, users_issues, integrations_issues, gamification_issues]
        for issue in issues if issue.get('severity') == 'warning'
    )

    # Overall status
    if critical_count > 0:
        status = 'CRITICAL'
        status_emoji = '🚨'
    elif error_count > 0:
        status = 'FAILED'
        status_emoji = '❌'
    elif warning_count > 0:
        status = 'WARNING'
        status_emoji = '⚠️'
    else:
        status = 'PASSED'
        status_emoji = '✅'

    report = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': context['execution_date'].isoformat(),
        'status': status,
        'summary': {
            'critical': critical_count,
            'error': error_count,
            'warning': warning_count,
            'total_issues': critical_count + error_count + warning_count,
        },
        'details': {
            'life_events': life_events_issues,
            'users': users_issues,
            'integrations': integrations_issues,
            'gamification': gamification_issues,
        },
        'generated_at': datetime.utcnow().isoformat(),
    }

    logger.info(f"{status_emoji} Data Quality Status: {status}")
    logger.info(f"📊 Issues - Critical: {critical_count}, Error: {error_count}, Warning: {warning_count}")

    # In production: Save report to database, send alerts
    # If critical, send alert to on-call engineer
    # If errors, create tickets
    # If warnings, log for review

    return report


# ==================== DAG DEFINITION ====================

with DAG(
    'data_quality_pipeline',
    default_args=default_args,
    description='Data quality monitoring and validation',
    schedule_interval='0 */4 * * *',  # Run every 4 hours
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['data-quality', 'monitoring', 'production'],
    max_active_runs=1,
) as dag:

    # Quality checks (parallel)
    check_life_events = PythonOperator(
        task_id='check_life_events_quality',
        python_callable=check_life_events_quality,
        provide_context=True,
    )

    check_users = PythonOperator(
        task_id='check_users_quality',
        python_callable=check_users_quality,
        provide_context=True,
    )

    check_integrations = PythonOperator(
        task_id='check_integrations_quality',
        python_callable=check_integrations_quality,
        provide_context=True,
    )

    check_gamification = PythonOperator(
        task_id='check_gamification_quality',
        python_callable=check_gamification_quality,
        provide_context=True,
    )

    # Generate report
    generate_report = PythonOperator(
        task_id='generate_quality_report',
        python_callable=generate_quality_report,
        provide_context=True,
    )

    # Define dependencies
    [check_life_events, check_users, check_integrations, check_gamification] >> generate_report
