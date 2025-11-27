# Aurora Life - Airflow ML Orchestration

Apache Airflow configuration for ML pipeline orchestration.

## 📋 Overview

Airflow orchestrates:
- **ML Model Training** (daily at 2 AM)
- **Feature Engineering** (every 6 hours)
- **Prediction Generation** (daily at 6 AM)
- **Data Quality Monitoring** (every 4 hours)

## 🚀 DAGs

### 1. ML Training Pipeline (`ml_training_pipeline`)

**Schedule:** Daily at 2:00 AM
**Purpose:** Train all ML models with latest data

**Tasks:**
1. Extract training data from PostgreSQL (90 days)
2. Engineer features (temporal, aggregations, derived metrics)
3. Train models in parallel:
   - Energy prediction model (XGBoost)
   - Mood prediction model (LightGBM)
   - Sleep quality prediction model
4. Publish training results to Kafka

**Outputs:**
- Updated models in Redis
- Training metrics
- Kafka events for monitoring

---

### 2. Feature Engineering Pipeline (`feature_engineering_pipeline`)

**Schedule:** Every 6 hours
**Purpose:** Compute and update features in Feature Store

**Tasks (Parallel):**
1. Compute user activity features (24h, 7d, 30d aggregations)
2. Compute sleep features (duration, consistency, debt)
3. Compute exercise features (frequency, intensity, variety)
4. Compute social features (engagement, friend count)
5. Update feature store (Redis/Feast)

**Features Computed:**
- `activity_count_24h`, `activity_count_7d`, `activity_count_30d`
- `activity_diversity_7d`, `total_minutes_7d`
- `avg_sleep_duration_7d`, `sleep_consistency_7d`, `sleep_debt_minutes`
- `exercise_count_7d`, `exercise_consistency_score`
- `friend_count`, `social_engagement_score`

---

### 3. Prediction Pipeline (`prediction_pipeline`)

**Schedule:** Daily at 6:00 AM
**Purpose:** Generate predictions for all active users

**Tasks:**
1. Get active users (premium/pro only)
2. Generate predictions in parallel:
   - **Energy predictions** (24h ahead, 2-hour intervals)
   - **Mood predictions** (daily)
   - **Sleep quality predictions** (tonight)
3. Save predictions to PostgreSQL
4. Cache predictions in Redis
5. Publish prediction events to Kafka

**Prediction Models:**
- Energy: Based on time of day, sleep quality, exercise
- Mood: Based on sleep, social engagement, activity diversity
- Sleep Quality: Based on consistency, debt, exercise, activity

---

### 4. Data Quality Pipeline (`data_quality_pipeline`)

**Schedule:** Every 4 hours
**Purpose:** Monitor data quality and detect issues

**Checks (Parallel):**

**Life Events:**
- No duplicates
- Valid timestamps (not future)
- Duration > 0 and < 24h
- Energy/mood levels in 1-10 range
- Required fields present

**Users:**
- Valid email formats
- No duplicate emails
- Valid subscription tiers
- Active status consistency

**Integrations:**
- Data freshness (< 48h)
- Valid provider names
- Sync success rate
- Data completeness

**Gamification:**
- No negative XP
- Level-XP consistency
- Valid achievement unlocks
- No orphaned records

**Outputs:**
- Quality report with severity levels (critical, error, warning)
- Alerts for critical issues
- Metrics for monitoring dashboard

---

## 🔧 Configuration

### Airflow Connections

Configure in Airflow UI (`Admin > Connections`):

**aurora_postgres:**
- Conn Type: `Postgres`
- Host: `postgres`
- Schema: `aurora_life`
- Login: `aurora`
- Password: `<from .env>`
- Port: `5432`

**aurora_redis:**
- Conn Type: `Redis`
- Host: `redis`
- Port: `6379`
- Password: `<from .env if set>`

### Environment Variables

Set in `docker-compose.yml`:

```yaml
AIRFLOW__CORE__EXECUTOR: CeleryExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://...
AIRFLOW__CELERY__BROKER_URL: redis://...
AIRFLOW__CELERY__RESULT_BACKEND: redis://...
```

---

## 📊 Monitoring

### Airflow UI

Access at: `http://localhost:8081`

**Dashboards:**
- DAG runs history
- Task duration trends
- Success/failure rates
- Resource utilization

### Metrics

Key metrics to monitor:
- DAG run duration
- Task success rate
- Data quality scores
- Model training metrics
- Prediction counts

### Alerts

Configure email alerts for:
- DAG failures
- Critical data quality issues
- Long-running tasks
- Resource exhaustion

---

## 🧪 Testing DAGs

### Trigger Manual Run

```bash
# Via CLI
docker exec -it aurora_airflow_webserver \
  airflow dags trigger ml_training_pipeline

# Or use Airflow UI
# Click DAG > Trigger DAG
```

### Test Individual Task

```bash
# Test specific task
docker exec -it aurora_airflow_webserver \
  airflow tasks test ml_training_pipeline extract_training_data 2025-01-27
```

### Backfill

```bash
# Backfill for date range
docker exec -it aurora_airflow_webserver \
  airflow dags backfill ml_training_pipeline \
  --start-date 2025-01-20 \
  --end-date 2025-01-27
```

---

## 🐛 Troubleshooting

### Check Logs

```bash
# Airflow scheduler logs
docker logs aurora_airflow_scheduler

# Airflow worker logs
docker logs aurora_airflow_worker

# Task logs (in UI)
# Click DAG > Task > View Log
```

### Common Issues

**Database connection failed:**
- Check PostgreSQL is running
- Verify connection string in Airflow UI
- Check network connectivity

**Redis connection failed:**
- Verify Redis is running
- Check Redis password in connection
- Verify port 6379 is accessible

**DAG not appearing:**
- Check DAG file for syntax errors
- Verify file is in `/airflow/dags/` directory
- Check scheduler logs for import errors

**Task stuck in queue:**
- Check Celery worker is running
- Verify Redis broker connection
- Check worker resource limits

---

## 📚 Development

### Adding New DAG

1. Create DAG file in `airflow/dags/`
2. Define `default_args`
3. Create DAG object with schedule
4. Add task operators
5. Define task dependencies
6. Test locally
7. Commit and deploy

### DAG Best Practices

- Use descriptive task IDs
- Set appropriate retries and timeouts
- Use XCom sparingly (for small data)
- Parallelize independent tasks
- Add proper logging
- Use tags for organization
- Set max_active_runs=1 for resource-intensive DAGs

### Custom Operators

Create custom operators in `airflow/plugins/`:

```python
# airflow/plugins/aurora_operators.py
from airflow.models import BaseOperator

class AuroraMLOperator(BaseOperator):
    def execute(self, context):
        # Custom logic
        pass
```

---

## 🔐 Security

### Access Control

Configure RBAC in Airflow:
- Admin: Full access
- ML Team: Trigger DAGs, view logs
- Ops Team: View only

### Secrets Management

Store secrets in:
1. Environment variables (docker-compose.yml)
2. Airflow Connections (encrypted in DB)
3. External secret manager (AWS Secrets Manager, etc.)

**Never** hardcode credentials in DAG files.

---

## 📈 Performance Optimization

### Parallelization

- Use parallel task execution where possible
- Set `max_active_tasks` appropriately
- Scale Celery workers based on load

### Resource Management

- Set task-level resource requirements
- Use pools for resource limiting
- Configure task queues for prioritization

### Data Handling

- Use external storage (S3, GCS) for large datasets
- Avoid large XCom payloads
- Stream data when possible

---

## 🔄 CI/CD Integration

### DAG Testing

```python
# tests/dags/test_ml_training_pipeline.py
import pytest
from airflow.models import DagBag

def test_dag_loaded():
    dagbag = DagBag(dag_folder='airflow/dags/')
    assert 'ml_training_pipeline' in dagbag.dags
    assert len(dagbag.import_errors) == 0

def test_dag_structure():
    dag = dagbag.get_dag('ml_training_pipeline')
    assert len(dag.tasks) == 6
    assert 'extract_training_data' in dag.task_ids
```

### Deployment

1. Test DAGs locally
2. Run unit tests
3. Deploy to staging
4. Verify in Airflow UI
5. Monitor first runs
6. Deploy to production

---

## 📞 Support

For issues or questions:
- Check Airflow logs
- Review task execution history
- Consult Airflow documentation
- Contact ML/Data team

---

**Last Updated:** 2025-01-27
**Version:** 1.0
**Maintained by:** Aurora ML Team
