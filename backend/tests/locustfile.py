"""
Load testing with Locust

Run with:
    locust -f tests/locustfile.py --host http://localhost:8000

For distributed load testing:
    # Master
    locust -f tests/locustfile.py --master --host http://localhost:8000

    # Workers
    locust -f tests/locustfile.py --worker --master-host=localhost
"""

from locust import HttpUser, task, between
from datetime import datetime, timezone
import random
import uuid


class AuroraLifeUser(HttpUser):
    """
    Simulates a typical AURORA_LIFE user.

    User behavior:
    - Logs in
    - Creates events
    - Views timeline
    - Gets predictions
    - Generates insights
    """

    # Wait 1-5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a simulated user starts."""
        # Register a new user for testing
        self.username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.password = "TestPass123!"

        response = self.client.post("/api/auth/register", json={
            "email": f"{self.username}@example.com",
            "username": self.username,
            "password": self.password
        })

        if response.status_code == 201:
            # Login to get token
            self.login()
        else:
            # User might already exist, try login
            self.login()

    def login(self):
        """Login and store access token."""
        response = self.client.post("/api/auth/login", json={
            "username": self.username,
            "password": self.password
        })

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
        else:
            # Fallback: use a pre-existing test user
            self.headers = {
                "Authorization": "Bearer dummy_token_for_testing"
            }

    @task(10)
    def create_sleep_event(self):
        """Create a sleep event (high frequency)."""
        self.client.post("/api/v1/events", json={
            "event_type": "sleep",
            "title": "Night sleep",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {
                "duration_hours": random.uniform(6, 9),
                "quality": random.choice(["poor", "fair", "good", "excellent"])
            }
        }, headers=self.headers, name="/api/v1/events [POST sleep]")

    @task(8)
    def create_exercise_event(self):
        """Create an exercise event."""
        self.client.post("/api/v1/events", json={
            "event_type": "exercise",
            "title": random.choice(["Morning run", "Gym workout", "Yoga session"]),
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {
                "duration_minutes": random.randint(20, 90),
                "intensity": random.choice(["light", "moderate", "intense"]),
                "calories": random.randint(100, 500)
            }
        }, headers=self.headers, name="/api/v1/events [POST exercise]")

    @task(6)
    def create_work_event(self):
        """Create a work event."""
        self.client.post("/api/v1/events", json={
            "event_type": "work",
            "title": "Work session",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {
                "duration_hours": random.uniform(1, 4),
                "focus_level": random.randint(1, 10),
                "tasks_completed": random.randint(1, 10)
            }
        }, headers=self.headers, name="/api/v1/events [POST work]")

    @task(5)
    def create_mood_event(self):
        """Create a mood event."""
        self.client.post("/api/v1/events", json={
            "event_type": "mood",
            "title": "Mood check-in",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {
                "mood_score": random.randint(1, 10),
                "energy_level": random.randint(1, 10),
                "stress_level": random.randint(1, 10),
                "notes": "Feeling " + random.choice(["great", "good", "okay", "tired", "stressed"])
            }
        }, headers=self.headers, name="/api/v1/events [POST mood]")

    @task(15)
    def list_events(self):
        """List recent events (high frequency)."""
        params = {
            "page": 1,
            "page_size": 20,
            "event_type": random.choice(["sleep", "exercise", "work", "mood", None])
        }
        self.client.get("/api/v1/events", params=params, headers=self.headers,
                       name="/api/v1/events [GET list]")

    @task(10)
    def get_timeline(self):
        """Get timeline view."""
        self.client.get("/api/v1/timeline", params={"days": 30}, headers=self.headers)

    @task(12)
    def get_energy_prediction(self):
        """Get energy prediction (high frequency)."""
        self.client.get("/api/v1/predictions/energy", headers=self.headers,
                       name="/api/v1/predictions/energy")

    @task(12)
    def get_mood_prediction(self):
        """Get mood prediction (high frequency)."""
        self.client.get("/api/v1/predictions/mood", headers=self.headers,
                       name="/api/v1/predictions/mood")

    @task(3)
    def generate_insights(self):
        """Generate AI insights (lower frequency due to cost)."""
        self.client.post("/api/v1/insights/generate", json={
            "context": random.choice(["health", "productivity", "wellbeing"]),
            "time_range_days": 7
        }, headers=self.headers, name="/api/v1/insights/generate")

    @task(5)
    def list_insights(self):
        """List existing insights."""
        self.client.get("/api/v1/insights", params={"page": 1, "page_size": 10},
                       headers=self.headers, name="/api/v1/insights [GET list]")

    @task(8)
    def get_user_profile(self):
        """Get user profile."""
        self.client.get("/api/v1/users/me", headers=self.headers)

    @task(2)
    def update_user_profile(self):
        """Update user profile (low frequency)."""
        self.client.put("/api/v1/users/me", json={
            "preferences": {
                "theme": random.choice(["light", "dark"]),
                "notifications_enabled": random.choice([True, False])
            }
        }, headers=self.headers, name="/api/v1/users/me [PUT]")

    @task(1)
    def health_check(self):
        """Health check endpoint (low frequency)."""
        self.client.get("/health")


class AdminUser(HttpUser):
    """
    Simulates an admin user with different access patterns.
    """

    wait_time = between(2, 10)

    def on_start(self):
        """Admin login."""
        # Use admin credentials
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"  # Should be in env var
        })

        if response.status_code == 200:
            data = response.json()
            self.headers = {
                "Authorization": f"Bearer {data['access_token']}"
            }

    @task(5)
    def list_all_users(self):
        """Admin: List all users."""
        self.client.get("/api/v1/admin/users", params={"page": 1, "page_size": 50},
                       headers=self.headers, name="/api/v1/admin/users")

    @task(3)
    def view_system_metrics(self):
        """Admin: View system metrics."""
        self.client.get("/metrics", headers=self.headers)

    @task(2)
    def detailed_health_check(self):
        """Admin: Detailed health check."""
        self.client.get("/health/detailed", headers=self.headers)

    @task(1)
    def trigger_model_retraining(self):
        """Admin: Trigger ML model retraining."""
        self.client.post("/api/v1/admin/ml/retrain", headers=self.headers,
                        name="/api/v1/admin/ml/retrain")


class APIOnlyUser(HttpUser):
    """
    Simulates SDK/API-only usage (no UI).
    Heavy on predictions and data retrieval.
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        """API user login."""
        self.api_key = "test_api_key_12345"  # Should be real API key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    @task(20)
    def batch_predictions(self):
        """Get both energy and mood predictions."""
        self.client.get("/api/v1/predictions/energy", headers=self.headers,
                       name="/api/v1/predictions/energy [SDK]")
        self.client.get("/api/v1/predictions/mood", headers=self.headers,
                       name="/api/v1/predictions/mood [SDK]")

    @task(10)
    def batch_event_creation(self):
        """Create multiple events in quick succession."""
        events = [
            {
                "event_type": "mood",
                "title": "Check-in",
                "event_time": datetime.now(timezone.utc).isoformat(),
                "event_data": {"mood_score": random.randint(1, 10)}
            }
            for _ in range(5)
        ]

        for event in events:
            self.client.post("/api/v1/events", json=event, headers=self.headers,
                           name="/api/v1/events [POST batch]")

    @task(15)
    def paginated_event_fetching(self):
        """Fetch events with pagination."""
        for page in range(1, 4):
            self.client.get("/api/v1/events",
                          params={"page": page, "page_size": 50},
                          headers=self.headers,
                          name="/api/v1/events [GET paginated]")


# Load test scenarios
class LightLoad(HttpUser):
    """Light load: 10-50 users"""
    tasks = [AuroraLifeUser]
    weight = 80


class MediumLoad(HttpUser):
    """Medium load: 50-200 users"""
    tasks = [AuroraLifeUser, AdminUser, APIOnlyUser]
    weight = 15


class HeavyLoad(HttpUser):
    """Heavy load: 200-1000 users"""
    tasks = [AuroraLifeUser, APIOnlyUser]
    weight = 5
