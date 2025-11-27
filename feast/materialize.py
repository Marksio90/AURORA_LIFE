"""
Feast Feature Materialization

Script to materialize features from offline to online store.
Run this periodically (via Airflow or cron) to keep features fresh.
"""
import logging
from datetime import datetime, timedelta
from feast import FeatureStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def materialize_features(
    start_date: datetime = None,
    end_date: datetime = None,
):
    """
    Materialize features from offline to online store.

    Args:
        start_date: Start of materialization window (default: 7 days ago)
        end_date: End of materialization window (default: now)
    """
    # Initialize feature store
    store = FeatureStore(repo_path=".")

    # Default time window
    if end_date is None:
        end_date = datetime.utcnow()

    if start_date is None:
        start_date = end_date - timedelta(days=7)

    logger.info(f"📊 Materializing features from {start_date} to {end_date}")

    try:
        # Materialize all feature views
        store.materialize(
            start_date=start_date,
            end_date=end_date,
        )

        logger.info("✅ Feature materialization completed successfully")

        # Get feature statistics
        stats = get_feature_stats(store)
        logger.info(f"📈 Feature Statistics:\n{stats}")

        return True

    except Exception as e:
        logger.error(f"❌ Feature materialization failed: {e}", exc_info=True)
        return False


def materialize_incremental():
    """
    Materialize features incrementally (since last materialization).

    This is more efficient for regular updates.
    """
    store = FeatureStore(repo_path=".")

    logger.info("📊 Materializing features incrementally...")

    try:
        store.materialize_incremental(
            end_date=datetime.utcnow()
        )

        logger.info("✅ Incremental materialization completed")
        return True

    except Exception as e:
        logger.error(f"❌ Incremental materialization failed: {e}", exc_info=True)
        return False


def get_feature_stats(store: FeatureStore) -> dict:
    """
    Get statistics about materialized features.
    """
    stats = {
        "feature_views": [],
        "feature_services": [],
    }

    # Get all feature views
    for fv in store.list_feature_views():
        stats["feature_views"].append({
            "name": fv.name,
            "features_count": len(fv.schema),
            "ttl_seconds": fv.ttl.total_seconds() if fv.ttl else None,
        })

    # Get all feature services
    for fs in store.list_feature_services():
        stats["feature_services"].append({
            "name": fs.name,
            "tags": fs.tags,
        })

    return stats


def get_online_features_example():
    """
    Example: Get online features for prediction.
    """
    store = FeatureStore(repo_path=".")

    # Example user IDs
    user_ids = ["user-123", "user-456", "user-789"]

    # Get features for energy prediction
    logger.info("🔍 Fetching online features for energy prediction...")

    features = store.get_online_features(
        features=[
            "user_activity_features:avg_energy_7d",
            "user_activity_features:total_minutes_7d",
            "sleep_features:sleep_quality_score",
            "exercise_features:exercise_consistency_score",
        ],
        entity_rows=[{"user_id": uid} for uid in user_ids],
    )

    # Convert to dict
    features_dict = features.to_dict()

    logger.info(f"✅ Retrieved features for {len(user_ids)} users")
    logger.info(f"Features: {features_dict}")

    return features_dict


def get_features_for_training():
    """
    Example: Get historical features for model training.
    """
    store = FeatureStore(repo_path=".")

    # Define entity dataframe (users and timestamps)
    from datetime import datetime
    import pandas as pd

    entity_df = pd.DataFrame({
        "user_id": ["user-123", "user-456", "user-789"] * 30,
        "event_timestamp": [
            datetime.utcnow() - timedelta(days=i)
            for i in range(30)
            for _ in range(3)
        ],
    })

    logger.info("🔍 Fetching historical features for training...")

    # Get historical features
    training_df = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "user_activity_features:avg_energy_7d",
            "user_activity_features:total_minutes_7d",
            "sleep_features:sleep_quality_score",
            "sleep_features:avg_sleep_duration_7d",
            "exercise_features:exercise_consistency_score",
            "exercise_features:exercise_minutes_7d",
            "social_features:social_engagement_score",
        ],
    ).to_df()

    logger.info(f"✅ Retrieved {len(training_df)} training samples")
    logger.info(f"Shape: {training_df.shape}")
    logger.info(f"Columns: {training_df.columns.tolist()}")

    return training_df


def push_features_realtime(user_id: str, features: dict):
    """
    Push real-time features to online store.

    Args:
        user_id: User ID
        features: Dict of feature values
    """
    store = FeatureStore(repo_path=".")

    # Create push data
    push_data = {
        "user_id": [user_id],
        "event_timestamp": [datetime.utcnow()],
        **{k: [v] for k, v in features.items()}
    }

    # Convert to DataFrame
    import pandas as pd
    df = pd.DataFrame(push_data)

    # Push to online store
    store.push("user_activity_push", df, to=PushMode.ONLINE)

    logger.info(f"✅ Pushed features for user {user_id}")


def main():
    """
    Main function - run materialization.
    """
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "incremental"

    logger.info(f"🚀 Starting feature materialization (mode: {mode})")

    if mode == "full":
        # Full materialization (last 7 days)
        success = materialize_features()
    elif mode == "incremental":
        # Incremental materialization
        success = materialize_incremental()
    elif mode == "example":
        # Run examples
        get_online_features_example()
        get_features_for_training()
        success = True
    else:
        logger.error(f"Unknown mode: {mode}")
        logger.info("Usage: python materialize.py [full|incremental|example]")
        success = False

    if success:
        logger.info("🎉 Feature store updated successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Feature store update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
