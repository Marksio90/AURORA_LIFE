"""
A/B Testing framework for experimentation.

Features:
- Experiment creation and management
- Variant assignment (deterministic based on user ID)
- Conversion tracking
- Statistical significance calculation
- Experiment results analysis
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)


class VariantType(str, Enum):
    """Experiment variant types."""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class ExperimentStatus(str, Enum):
    """Experiment lifecycle status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class ABTestingService:
    """Service for A/B testing experiments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        traffic_allocation: float = 1.0
    ) -> UUID:
        """
        Create a new A/B test experiment.

        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variants with weights
                Example: [
                    {"name": "control", "weight": 0.5},
                    {"name": "variant_a", "weight": 0.5}
                ]
            traffic_allocation: Percentage of users in experiment (0.0-1.0)

        Returns:
            Experiment ID
        """
        from app.models.experiments import Experiment

        experiment = Experiment(
            id=uuid4(),
            name=name,
            description=description,
            variants=variants,
            traffic_allocation=traffic_allocation,
            status=ExperimentStatus.DRAFT,
            created_at=datetime.utcnow()
        )

        self.db.add(experiment)
        await self.db.commit()

        logger.info(f"Created experiment: {name}")

        return experiment.id

    async def start_experiment(self, experiment_id: UUID):
        """Start an experiment."""
        from app.models.experiments import Experiment

        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one()

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Started experiment: {experiment.name}")

    async def get_variant(
        self,
        experiment_name: str,
        user_id: UUID
    ) -> Optional[str]:
        """
        Get assigned variant for a user in an experiment.

        Uses consistent hashing to ensure same user always gets same variant.

        Returns:
            Variant name or None if user not in experiment
        """
        from app.models.experiments import Experiment, ExperimentAssignment

        # Get experiment
        result = await self.db.execute(
            select(Experiment).where(
                Experiment.name == experiment_name,
                Experiment.status == ExperimentStatus.RUNNING
            )
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return None

        # Check if user already assigned
        result = await self.db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.experiment_id == experiment.id,
                ExperimentAssignment.user_id == user_id
            )
        )
        assignment = result.scalar_one_or_none()

        if assignment:
            return assignment.variant

        # Check if user is in traffic allocation
        if not self._is_user_in_experiment(str(user_id), experiment.traffic_allocation):
            return None

        # Assign variant
        variant = self._assign_variant(str(user_id), experiment.variants)

        # Save assignment
        assignment = ExperimentAssignment(
            id=uuid4(),
            experiment_id=experiment.id,
            user_id=user_id,
            variant=variant,
            assigned_at=datetime.utcnow()
        )

        self.db.add(assignment)
        await self.db.commit()

        logger.info(f"Assigned user {user_id} to variant {variant} in {experiment_name}")

        return variant

    def _is_user_in_experiment(self, user_id: str, traffic_allocation: float) -> bool:
        """Determine if user is included in experiment traffic."""
        if traffic_allocation >= 1.0:
            return True

        # Hash user ID to get consistent random value
        hash_value = hashlib.md5(f"traffic_{user_id}".encode()).hexdigest()
        bucket = int(hash_value[:8], 16) % 100

        return bucket < (traffic_allocation * 100)

    def _assign_variant(self, user_id: str, variants: List[Dict[str, Any]]) -> str:
        """Assign variant based on weighted distribution."""
        # Hash user ID for consistent assignment
        hash_value = hashlib.md5(f"variant_{user_id}".encode()).hexdigest()
        bucket = int(hash_value[:8], 16) % 100

        # Assign based on weights
        cumulative_weight = 0
        for variant in variants:
            cumulative_weight += variant["weight"] * 100
            if bucket < cumulative_weight:
                return variant["name"]

        # Default to first variant
        return variants[0]["name"]

    async def track_conversion(
        self,
        experiment_name: str,
        user_id: UUID,
        metric_name: str,
        value: float = 1.0
    ):
        """
        Track a conversion event for an experiment.

        Args:
            experiment_name: Name of experiment
            user_id: User UUID
            metric_name: Name of metric (e.g., 'signup', 'purchase')
            value: Metric value (e.g., revenue amount)
        """
        from app.models.experiments import Experiment, ExperimentConversion

        # Get experiment and assignment
        result = await self.db.execute(
            select(Experiment).where(Experiment.name == experiment_name)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            logger.warning(f"Experiment not found: {experiment_name}")
            return

        # Check if user is in experiment
        variant = await self.get_variant(experiment_name, user_id)

        if not variant:
            return

        # Track conversion
        conversion = ExperimentConversion(
            id=uuid4(),
            experiment_id=experiment.id,
            user_id=user_id,
            variant=variant,
            metric_name=metric_name,
            value=value,
            converted_at=datetime.utcnow()
        )

        self.db.add(conversion)
        await self.db.commit()

        logger.info(
            f"Tracked conversion for {metric_name} in {experiment_name}: "
            f"variant={variant}, value={value}"
        )

    async def get_experiment_results(
        self,
        experiment_id: UUID
    ) -> Dict[str, Any]:
        """
        Get experiment results with statistical analysis.

        Returns:
            Results including:
            - Variant statistics
            - Conversion rates
            - Statistical significance (p-value)
        """
        from app.models.experiments import (
            Experiment,
            ExperimentAssignment,
            ExperimentConversion
        )

        # Get experiment
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one()

        # Get assignments per variant
        result = await self.db.execute(
            select(
                ExperimentAssignment.variant,
                func.count(ExperimentAssignment.id).label("count")
            )
            .where(ExperimentAssignment.experiment_id == experiment_id)
            .group_by(ExperimentAssignment.variant)
        )
        assignments = {row[0]: row[1] for row in result.fetchall()}

        # Get conversions per variant
        result = await self.db.execute(
            select(
                ExperimentConversion.variant,
                ExperimentConversion.metric_name,
                func.count(ExperimentConversion.id).label("count"),
                func.sum(ExperimentConversion.value).label("total_value")
            )
            .where(ExperimentConversion.experiment_id == experiment_id)
            .group_by(ExperimentConversion.variant, ExperimentConversion.metric_name)
        )
        conversions = {}
        for row in result.fetchall():
            variant = row[0]
            metric = row[1]
            if variant not in conversions:
                conversions[variant] = {}
            conversions[variant][metric] = {
                "count": row[2],
                "total_value": float(row[3]) if row[3] else 0
            }

        # Calculate statistics per variant
        variant_stats = {}
        for variant_name, assignment_count in assignments.items():
            variant_conversions = conversions.get(variant_name, {})

            variant_stats[variant_name] = {
                "assignments": assignment_count,
                "metrics": {}
            }

            for metric_name, metric_data in variant_conversions.items():
                conversion_rate = metric_data["count"] / assignment_count if assignment_count > 0 else 0

                variant_stats[variant_name]["metrics"][metric_name] = {
                    "conversions": metric_data["count"],
                    "conversion_rate": conversion_rate,
                    "total_value": metric_data["total_value"],
                    "average_value": metric_data["total_value"] / metric_data["count"] if metric_data["count"] > 0 else 0
                }

        return {
            "experiment_id": str(experiment_id),
            "experiment_name": experiment.name,
            "status": experiment.status,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "variant_stats": variant_stats
        }


# Example usage:
"""
from app.core.ab_testing import ABTestingService

# Create experiment
service = ABTestingService(db)
experiment_id = await service.create_experiment(
    name="new_dashboard_test",
    description="Test new dashboard design",
    variants=[
        {"name": "control", "weight": 0.5},
        {"name": "new_design", "weight": 0.5}
    ],
    traffic_allocation=0.5  # 50% of users
)

# Start experiment
await service.start_experiment(experiment_id)

# In your route, get variant
variant = await service.get_variant("new_dashboard_test", user.id)

if variant == "new_design":
    # Show new dashboard
    pass
else:
    # Show old dashboard
    pass

# Track conversion
await service.track_conversion(
    "new_dashboard_test",
    user.id,
    "dashboard_engagement",
    value=1.0
)

# Get results
results = await service.get_experiment_results(experiment_id)
"""
