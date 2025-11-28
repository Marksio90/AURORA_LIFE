# 🌅 Aurora Life

**Your Digital Life Companion - Track, Analyze, and Optimize Your Life**

Aurora Life is a comprehensive life tracking and optimization platform that combines advanced analytics, machine learning, gamification, and real-time insights to help you understand and improve your daily life.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.2+-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)

---

## 🚀 Features

### 📊 Core Features
- **Life Event Tracking** - Log activities, sleep, exercise, work, social events
- **Timeline View** - Visual timeline of your life events
- **Categories & Tags** - Organize events with custom categories and tags
- **Energy & Mood Tracking** - Track your energy and mood levels (1-10 scale)
- **Duration Tracking** - Automatic or manual time tracking

### 🤖 AI & Machine Learning
- **Predictive Analytics** - ML models predict energy, mood, sleep quality
- **Smart Insights** - Automatic pattern detection and personalized insights
- **Trend Analysis** - Linear regression, correlations, anomaly detection
- **Personalized Recommendations** - AI-driven suggestions based on your data
- **Feature Store** - Feast-powered feature management for ML
- **ML Orchestration** - Apache Airflow DAGs for model training

### 📈 Advanced Analytics
- **Time Series Analysis** - Track metrics over time with multiple granularities
- **Statistical Analysis** - Mean, median, std, percentiles, z-scores
- **Correlation Detection** - Discover relationships between activities
- **Anomaly Detection** - Identify unusual patterns automatically
- **Wellness Reports** - Comprehensive wellness scores (0-100)
- **Progress Reports** - Goal tracking and achievement analytics

### 🎮 Gamification & Social
- **XP & Leveling System** - Earn XP, level up, unlock rewards
- **Achievements** - 50+ achievements to unlock
- **Streaks** - Daily activity streaks with rewards
- **Leaderboards** - Compete with friends (coming soon)
- **Social Feed** - Share posts, like, comment
- **Friends System** - Connect with other users
- **Challenges** - Compete in daily/weekly challenges

### 🔗 Integrations
- **Fitbit** - Sync sleep, heart rate, steps, activities
- **Oura Ring** - Sleep tracking, readiness, HRV
- **Google Fit** - Activity and health data
- **Apple Health** - Comprehensive health metrics
- **Spotify** - Music listening habits
- **Google Calendar** - Event sync

### 🔔 Notifications & Real-time
- **WebSocket Support** - Real-time notification delivery
- **Email Notifications** - Beautiful HTML email templates
- **In-app Notifications** - Persistent notification center
- **Daily Digests** - Batch notifications once daily
- **Weekly Summaries** - Comprehensive weekly reports
- **Preference Management** - Granular notification controls
- **Quiet Hours** - Do not disturb during sleep

### 🔐 Security & Privacy
- **JWT Authentication** - Secure token-based auth
- **OAuth 2.0** - Google, GitHub, Facebook login
- **Role-based Access** - User, admin, moderator roles
- **Data Encryption** - Encrypted sensitive data
- **Privacy Controls** - Granular data sharing controls

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- **FastAPI** - Modern, fast web framework
- **Python 3.11+** - Latest Python features
- **PostgreSQL 15** - Primary database
- **Redis 7.2** - Caching and real-time features
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **Celery** - Distributed task queue
- **Apache Kafka** - Event streaming
- **Apache Airflow** - ML orchestration
- **Feast** - Feature store for ML

**Machine Learning:**
- **scikit-learn** - Classical ML algorithms
- **XGBoost** - Gradient boosting
- **LightGBM** - Fast gradient boosting
- **Prophet** - Time series forecasting
- **TensorFlow** - Deep learning
- **PyTorch** - Neural networks
- **SHAP** - Model explainability
- **Optuna** - Hyperparameter tuning
- **MLflow** - ML experiment tracking

**AI & LLM:**
- **LangChain** - LLM orchestration
- **OpenAI API** - GPT models
- **Anthropic Claude** - Claude models
- **ChromaDB** - Vector database
- **Qdrant** - Vector search

**Data Engineering:**
- **Apache Kafka** - Event streaming (7.5.0)
- **Apache Airflow** - Workflow orchestration (2.8.1)
- **Feast** - Feature store (0.36.0)
- **Great Expectations** - Data quality
- **Pandera** - Data validation

**DevOps:**
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy & load balancing
- **Flower** - Celery monitoring
- **Prometheus** - Metrics (planned)
- **Grafana** - Dashboards (planned)

---

## 📁 Project Structure

```
AURORA_LIFE/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py              # Authentication endpoints
│   │   │       ├── users.py             # User management
│   │   │       ├── events.py            # Life events CRUD
│   │   │       ├── timeline.py          # Timeline views
│   │   │       ├── vault.py             # Data vault
│   │   │       ├── ai.py                # AI/LLM endpoints
│   │   │       ├── analytics.py         # Analytics & insights
│   │   │       └── notifications.py     # Notification system
│   │   ├── models/
│   │   │   ├── user.py                  # User model
│   │   │   ├── life_event.py            # Life event model
│   │   │   ├── gamification.py          # Gamification models
│   │   │   ├── social.py                # Social models
│   │   │   ├── integration.py           # Integration models
│   │   │   └── notification.py          # Notification models
│   │   ├── analytics/
│   │   │   ├── engine.py                # Analytics engine
│   │   │   ├── insights.py              # Insight generation
│   │   │   ├── trends.py                # Trend analysis
│   │   │   ├── recommendations.py       # Recommendation engine
│   │   │   ├── reports.py               # Report generation
│   │   │   └── README.md
│   │   ├── notifications/
│   │   │   ├── service.py               # Notification CRUD
│   │   │   ├── websocket.py             # WebSocket manager
│   │   │   ├── email.py                 # Email service
│   │   │   ├── helpers.py               # Notification helpers
│   │   │   └── README.md
│   │   ├── events/
│   │   │   ├── producer.py              # Kafka event producer
│   │   │   ├── consumer.py              # Kafka event consumer
│   │   │   └── schemas.py               # Event schemas
│   │   ├── core/
│   │   │   ├── config.py                # Configuration
│   │   │   ├── database.py              # Database setup
│   │   │   ├── auth.py                  # Auth utilities
│   │   │   └── security.py              # Security utils
│   │   └── main.py                      # FastAPI app
│   ├── alembic/                         # Database migrations
│   ├── tests/                           # Test suite
│   └── requirements.txt                 # Python dependencies
├── airflow/
│   ├── dags/
│   │   ├── ml_training_pipeline.py      # Model training
│   │   ├── feature_engineering_pipeline.py  # Feature computation
│   │   ├── prediction_pipeline.py       # Daily predictions
│   │   └── data_quality_pipeline.py     # Data quality checks
│   ├── logs/                            # Airflow logs
│   ├── plugins/                         # Custom plugins
│   └── airflow.cfg                      # Airflow config
├── feast/
│   ├── feature_store.yaml               # Feature store config
│   ├── features.py                      # Feature definitions
│   ├── data_sources.py                  # Data sources
│   └── materialize.py                   # Materialization script
├── nginx/
│   ├── nginx.conf                       # Main config
│   └── conf.d/
│       └── backend.conf                 # Backend proxy
├── docs/                                # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   └── INFRASTRUCTURE_SETUP_COMPLETE.md
├── docker-compose.yml                   # Docker Compose setup
├── .env.example                         # Environment template
├── Makefile                             # Automation commands
└── README.md                            # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (or use Docker)
- Redis 7.2+ (or use Docker)

### 1. Clone Repository

```bash
git clone https://github.com/Marksio90/AURORA_LIFE.git
cd AURORA_LIFE
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Quick Start (Docker)

```bash
# Quick start - launches full stack
make quickstart

# Or manually:
make build      # Build containers
make up         # Start services
make migrate    # Run migrations
make seed       # Seed initial data
```

### 4. Access Services

- **API Documentation:** http://localhost:8000/docs
- **Airflow UI:** http://localhost:8081 (user: admin, password: admin)
- **Kafka UI:** http://localhost:8080
- **Flower (Celery):** http://localhost:5555

### 5. Create Admin User

```bash
make create-admin
# Follow prompts to create admin account
```

---

## 📚 API Documentation

### Interactive API Docs

FastAPI provides interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Main Endpoints

**Authentication:**
```
POST   /api/v1/auth/register          # Register new user
POST   /api/v1/auth/login             # Login with credentials
POST   /api/v1/auth/refresh           # Refresh access token
POST   /api/v1/auth/logout            # Logout
GET    /api/v1/auth/me                # Get current user
```

**Life Events:**
```
GET    /api/v1/events                 # List events (paginated)
POST   /api/v1/events                 # Create event
GET    /api/v1/events/{id}            # Get event
PUT    /api/v1/events/{id}            # Update event
DELETE /api/v1/events/{id}            # Delete event
```

**Analytics:**
```
POST   /api/v1/analytics/query        # Execute analytics query
GET    /api/v1/analytics/time-series/{metric}  # Time series
GET    /api/v1/analytics/trends/{metric}       # Trend analysis
POST   /api/v1/analytics/correlations          # Correlations
GET    /api/v1/analytics/insights              # Generate insights
GET    /api/v1/analytics/recommendations       # Get recommendations
GET    /api/v1/analytics/reports/wellness      # Wellness report
```

**Notifications:**
```
GET    /api/v1/notifications          # List notifications
POST   /api/v1/notifications/{id}/read  # Mark as read
POST   /api/v1/notifications/read-all   # Mark all read
WS     /api/v1/notifications/ws         # WebSocket connection
GET    /api/v1/notifications/preferences/me  # Get preferences
PUT    /api/v1/notifications/preferences/me  # Update preferences
```

See full API documentation at `/docs` when server is running.

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_analytics.py

# Run with coverage
make test-coverage

# Run linting
make lint
```

---

## 🔧 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Database Migrations

```bash
# Create new migration
make migration-create name="add_new_table"

# Apply migrations
make migrate

# Rollback last migration
make migrate-down
```

### Docker Commands

```bash
make build          # Build containers
make up             # Start services
make down           # Stop services
make logs           # View logs
make shell          # Backend shell
make db-shell       # Database shell
make redis-shell    # Redis shell
```

### Data Engineering

```bash
# Start Airflow (with all dependencies)
make airflow-up

# Start Kafka ecosystem
make kafka-up

# Materialize features to Feast
cd feast && python materialize.py incremental
```

---

## 📊 Monitoring & Observability

### Logs

```bash
# View all logs
make logs

# View specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f airflow-scheduler
```

### Metrics

- **Celery Tasks:** http://localhost:5555 (Flower)
- **Airflow DAGs:** http://localhost:8081
- **Kafka Topics:** http://localhost:8080

---

## 🗄️ Database

### Schema

Aurora Life uses PostgreSQL with the following main tables:

- **users** - User accounts and profiles
- **life_events** - All tracked life events
- **user_profiles** - Gamification data (XP, levels, streaks)
- **achievements** - Achievement definitions
- **user_achievements** - Unlocked achievements
- **goals** - User goals
- **posts** - Social posts
- **friendships** - Friend connections
- **user_integrations** - External service integrations
- **integration_data** - Synced integration data
- **notifications** - User notifications
- **notification_preferences** - Notification settings

### Backups

```bash
# Backup database
make db-backup

# Restore from backup
make db-restore backup=backup_2025-01-27.sql
```

---

## 📖 Documentation

- **[Analytics Module](backend/app/analytics/README.md)** - Analytics, insights, trends, recommendations
- **[Notifications Module](backend/app/notifications/README.md)** - Notification system, WebSocket, email
- **[Airflow DAGs](airflow/README.md)** - ML orchestration, feature engineering
- **[Feast Feature Store](feast/README.md)** - Feature management for ML
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Infrastructure Setup](docs/INFRASTRUCTURE_SETUP_COMPLETE.md)** - Infrastructure overview

---

## 🎯 Roadmap

### ✅ Completed Phases

- **Phase 1-6:** Core functionality, authentication, life events, timeline
- **Phase 7:** ML/AI enhancement (models, predictions, insights)
- **Phase 8:** Gamification, social features, integrations
- **Phase 9:** Data engineering (Kafka, Airflow, Feast)
- **Phase 10:** Advanced analytics & insights
- **Phase 11:** Notifications & real-time updates

### 🚧 In Progress

- **Phase 12:** Testing & quality assurance
- **Phase 13:** Admin panel & monitoring

### 📋 Planned

- **Phase 14:** Mobile app support
- **Phase 15:** Advanced gamification (leaderboards, challenges)
- **Phase 16:** AI chat assistant
- **Phase 17:** Goal planning & tracking
- **Phase 18:** Data export & GDPR compliance
- **Phase 19:** Premium features & monetization
- **Phase 20:** Performance optimization

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for all functions
- Add tests for new features
- Run linting before committing

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Authors

- **Marksio90** - *Initial work* - [GitHub](https://github.com/Marksio90)

---

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- The open-source community for incredible tools
- All contributors and testers

---

## 📧 Contact

- **GitHub Issues:** [Report bugs or request features](https://github.com/Marksio90/AURORA_LIFE/issues)
- **Email:** your-email@example.com
- **Discord:** Coming soon

---

## 📊 Project Stats

- **Languages:** Python, SQL, YAML, Markdown
- **Total Lines of Code:** 50,000+ lines
- **API Endpoints:** 100+ endpoints
- **Database Tables:** 25+ tables
- **ML Models:** 5+ trained models
- **Features:** 200+ features in Feature Store
- **Achievements:** 50+ achievements
- **Integrations:** 6 external services

---

## 🌟 Star History

If you find Aurora Life useful, please consider giving it a star! ⭐

---

**Built with ❤️ using FastAPI, PostgreSQL, Redis, and a lot of coffee ☕**

🌅 **Aurora Life** - *Track your life, optimize your future.*
