# AURORA LIFE - Deployment Guide 🚀

Complete guide for deploying AURORA LIFE to development, staging, and production environments.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Development)](#quick-start-development)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Database Setup](#database-setup)
- [OAuth Configuration](#oauth-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software

- **Docker** 24.0+ & **Docker Compose** 2.20+
- **Git** 2.40+
- **Make** (optional, for convenience commands)

### Required API Keys

Before deploying, obtain the following API keys:

1. **OpenAI** (for Whisper voice API): https://platform.openai.com/
2. **Google Calendar** (optional): https://console.cloud.google.com/
3. **Fitbit** (optional): https://dev.fitbit.com/
4. **Oura Ring** (optional): https://cloud.ouraring.com/
5. **Spotify** (optional): https://developer.spotify.com/

---

## 🚀 Quick Start (Development)

Get up and running in 5 minutes:

```bash
# 1. Clone repository
git clone https://github.com/your-org/AURORA_LIFE.git
cd AURORA_LIFE

# 2. Quick start (builds, migrates, seeds)
make quickstart

# 3. Access services
open http://localhost:8000/docs  # API Documentation
```

**That's it!** All services are running:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery): http://localhost:5555 (admin/admin)
- Qdrant: http://localhost:6333

---

## ⚙️ Environment Setup

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Essential Variables

Edit `.env` and update at minimum:

```bash
# Security (REQUIRED)
SECRET_KEY=<generate with: openssl rand -base64 32>
JWT_SECRET_KEY=<generate with: openssl rand -base64 32>

# Database (use defaults for dev)
POSTGRES_PASSWORD=<change in production>

# Redis
REDIS_PASSWORD=<set in production>

# OpenAI (for voice interface)
OPENAI_API_KEY=sk-...

# Celery Monitoring
FLOWER_PASSWORD=<change from 'admin'>
```

### 3. Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🐳 Docker Deployment

### Development Mode

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Mode

```bash
# Start with Nginx reverse proxy
docker-compose --profile production up -d

# Services available at:
# - http://localhost (Nginx proxies to backend)
# - http://localhost/api/ (API endpoints)
# - http://localhost/flower/ (Celery monitoring)
```

### Individual Services

```bash
# Start only specific services
docker-compose up -d postgres redis backend

# Scale Celery workers
docker-compose up -d --scale celery_worker=8
```

---

## 🗄️ Database Setup

### Run Migrations

```bash
# Automatic (happens on startup)
docker-compose up -d

# Manual
make migrate
# or
docker-compose exec backend alembic upgrade head
```

### Seed Initial Data

```bash
# Seed gamification data (achievements, badges, challenges)
make seed
# or
docker-compose exec backend python -m app.db.seed_gamification
```

### Create Custom Migration

```bash
make migrate-create MSG="add new table"
# or
docker-compose exec backend alembic revision --autogenerate -m "add new table"
```

### Database Backup

```bash
# Backup
make backup-db

# Restore
make restore-db FILE=backups/backup_20241127_120000.sql
```

---

## 🔐 OAuth Configuration

For each integration, configure OAuth redirect URIs in the provider's dashboard:

### Google Calendar

1. Go to: https://console.cloud.google.com/
2. Create project → Enable Calendar API
3. Create OAuth 2.0 credentials
4. Add redirect URI: `http://localhost:8000/api/v1/integrations/google_calendar/callback`
5. Add to `.env`:
   ```bash
   GOOGLE_CALENDAR_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CALENDAR_CLIENT_SECRET=your-secret
   ```

### Fitbit

1. Go to: https://dev.fitbit.com/apps/new
2. Register application
3. OAuth 2.0 Application Type: **Server**
4. Redirect URL: `http://localhost:8000/api/v1/integrations/fitbit/callback`
5. Default Access Type: **Read-Only**
6. Add to `.env`:
   ```bash
   FITBIT_CLIENT_ID=your-client-id
   FITBIT_CLIENT_SECRET=your-secret
   ```

### Oura Ring

1. Go to: https://cloud.ouraring.com/oauth/applications
2. Create new application
3. Redirect URI: `http://localhost:8000/api/v1/integrations/oura/callback`
4. Add to `.env`:
   ```bash
   OURA_CLIENT_ID=your-client-id
   OURA_CLIENT_SECRET=your-secret
   ```

### Spotify

1. Go to: https://developer.spotify.com/dashboard
2. Create app
3. Redirect URI: `http://localhost:8000/api/v1/integrations/spotify/callback`
4. Add to `.env`:
   ```bash
   SPOTIFY_CLIENT_ID=your-client-id
   SPOTIFY_CLIENT_SECRET=your-secret
   ```

**Production:** Replace `http://localhost:8000` with your production domain.

---

## 📊 Monitoring Setup

### Flower (Celery Monitoring)

Access Flower at: http://localhost:5555

Default credentials (change in production):
- Username: `admin`
- Password: `admin`

Update in `.env`:
```bash
FLOWER_USER=your-username
FLOWER_PASSWORD=your-secure-password
```

### Health Checks

```bash
# Check all services
make health

# Manual checks
curl http://localhost:8000/health
curl http://localhost:6333/health  # Qdrant
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# All logs
make logs

# Specific service
make logs-backend
make logs-celery
make logs-db

# Follow logs
docker-compose logs -f celery_worker
```

### Sentry (Error Tracking)

1. Sign up at: https://sentry.io/
2. Create project
3. Add to `.env`:
   ```bash
   SENTRY_DSN=https://...@sentry.io/...
   SENTRY_ENVIRONMENT=production
   ```

### OpenTelemetry (Distributed Tracing)

For production observability:

```bash
# Optional: Configure OTEL exporter
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
OTEL_SERVICE_NAME=aurora-life-backend
```

---

## 🌐 Production Deployment

### Pre-Deployment Checklist

- [ ] All `.env` variables set
- [ ] Secure passwords generated
- [ ] OAuth redirect URIs updated to production domain
- [ ] SSL certificates obtained
- [ ] Database backups configured
- [ ] Monitoring/alerts configured
- [ ] Load testing completed
- [ ] Security scan passed

### Deployment Steps

#### 1. Build Production Images

```bash
# Set production environment
export APP_ENV=production
export INSTALL_DEV=false

# Build images
docker-compose --profile production build
```

#### 2. Update Nginx SSL Configuration

Edit `nginx/conf.d/backend.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... rest of config
}
```

#### 3. Deploy with SSL

```bash
# Start with Nginx (includes SSL)
docker-compose --profile production up -d

# Verify SSL
curl https://your-domain.com/health
```

#### 4. Scale for Production

```bash
# Scale workers based on load
docker-compose up -d --scale celery_worker=8

# Update worker count in .env
CELERY_WORKERS=8
```

### Cloud Platforms

#### AWS ECS

```bash
# 1. Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
docker tag aurora-life-backend:latest <ecr-url>/aurora-life-backend:latest
docker push <ecr-url>/aurora-life-backend:latest

# 2. Update ECS task definition
# 3. Deploy to ECS service
```

#### Google Cloud Run

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/<project-id>/aurora-life-backend

# 2. Deploy to Cloud Run
gcloud run deploy aurora-life \
  --image gcr.io/<project-id>/aurora-life-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### DigitalOcean App Platform

```yaml
# app.yaml
name: aurora-life
services:
  - name: backend
    dockerfile_path: backend/Dockerfile
    github:
      repo: your-org/AURORA_LIFE
      branch: main
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
```

### Database Migration (Production)

```bash
# Backup before migration
make backup-db

# Run migration
docker-compose exec backend alembic upgrade head

# Verify
docker-compose exec backend alembic current
```

### Zero-Downtime Deployment

```bash
# 1. Pull new images
docker-compose pull

# 2. Rolling update (one service at a time)
docker-compose up -d --no-deps --build backend
sleep 30  # Wait for health check
docker-compose up -d --no-deps --build celery_worker

# 3. Verify
make health
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U aurora -d aurora_life -c "SELECT 1"

# Solution: Wait for database to be ready
docker-compose exec backend python -m app.core.wait_for_db
```

#### 2. Migrations Failed

```bash
# Check current version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Rollback and retry
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

#### 3. Celery Tasks Not Running

```bash
# Check worker status
docker-compose logs celery_worker

# Check Flower
open http://localhost:5555

# Purge stuck tasks
make celery-purge

# Restart worker
docker-compose restart celery_worker celery_beat
```

#### 4. OAuth Integration Failing

```bash
# Check redirect URI matches exactly
echo $GOOGLE_CALENDAR_REDIRECT_URI

# Verify credentials
docker-compose exec backend python -c "from app.core.config import settings; print(settings.GOOGLE_CALENDAR_CLIENT_ID)"

# Check integration logs
docker-compose logs backend | grep -i "integration"
```

#### 5. High Memory Usage

```bash
# Check container stats
docker stats

# Reduce Celery workers
docker-compose up -d --scale celery_worker=2

# Update in .env
CELERY_WORKERS=2
```

### Health Check Failures

```bash
# 1. Check service health
make health

# 2. Check individual endpoints
curl http://localhost:8000/health
curl http://localhost:6333/health

# 3. Restart unhealthy service
docker-compose restart <service-name>
```

### Performance Issues

```bash
# 1. Check resource usage
docker stats

# 2. Profile application
docker-compose exec backend py-spy record -o profile.svg -- python -m app.main

# 3. Enable query logging
# Add to .env:
LOG_LEVEL=DEBUG

# 4. Check Celery queue length
docker-compose exec celery_worker celery -A app.core.celery_app inspect active
```

---

## 📖 Additional Resources

- [Phase 8 Usage Guide](./PHASE_8_USAGE_GUIDE.md) - Feature documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Makefile Commands](../Makefile) - All available commands
- [Docker Compose Config](../docker-compose.yml) - Service definitions

---

## 🆘 Support

**Issues:** https://github.com/your-org/AURORA_LIFE/issues

**For help:**
1. Check logs: `make logs`
2. Run health checks: `make health`
3. Review this guide
4. Open GitHub issue with details

---

**Last Updated:** November 27, 2024
**Version:** 1.0.0
