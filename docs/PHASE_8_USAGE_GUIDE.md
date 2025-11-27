# Phase 8 - Platform Features Usage Guide

Complete guide for using AURORA_LIFE's gamification, social, and integration features.

## 📋 Table of Contents

- [Gamification System](#gamification-system)
- [Social Features](#social-features)
- [Voice Interface](#voice-interface)
- [External Integrations](#external-integrations)
- [Background Tasks](#background-tasks)
- [API Endpoints](#api-endpoints)
- [Setup & Configuration](#setup--configuration)

---

## 🎮 Gamification System

### Overview

The gamification system motivates users through XP progression, achievements, badges, streaks, daily challenges, and leaderboards.

### XP & Leveling

**How It Works:**
- Users earn XP (Experience Points) from completing activities
- XP accumulates to increase user level
- Formula: `XP_required = 100 * level^1.5`

**XP Sources:**
- Logging life events: 10-50 XP
- Completing daily challenges: 25-100 XP
- Unlocking achievements: 25-500 XP
- Streak milestones: 50-200 XP
- Weekend bonus: 1.5x multiplier
- Streak multiplier: up to 2.0x

**API Endpoints:**
```bash
# Get user gamification stats
GET /api/v1/gamification/stats

# Award XP to user
POST /api/v1/gamification/xp/award
{
  "amount": 50,
  "source": "meditation_session",
  "metadata": {"duration": 15}
}
```

### Achievements

**Categories:**
- **Health**: Sleep, exercise, nutrition, meditation
- **Consistency**: Login streaks, challenge completions
- **Social**: Friends, groups, community engagement
- **Milestone**: Level ups, total events logged

**Example Achievements:**
- **Early Bird** (Common): Wake up before 6 AM for 7 days → 150 points, 100 XP
- **Sleep Champion** (Rare): Get 8+ hours sleep for 30 days → 500 points, 300 XP
- **Century Streak** (Legendary): 100-day login streak → 2000 points, 1000 XP

**API Endpoints:**
```bash
# List all achievements
GET /api/v1/gamification/achievements

# Get user's achievements
GET /api/v1/gamification/achievements/user

# Check achievement progress
GET /api/v1/gamification/achievements/{achievement_id}/progress
```

### Badges

Badges are special awards for exceptional accomplishments:

- **Founder**: First 1000 users (Gold)
- **Sleep Expert**: 90 days excellent sleep (Blue)
- **Fitness Legend**: 500 workout sessions (Red)
- **Zen Master**: 365 meditation sessions (Teal)
- **Streak Legend**: 365-day login streak (Orange)
- **Champion**: #1 on all-time leaderboard (Gold)

**API Endpoints:**
```bash
# List all badges
GET /api/v1/gamification/badges

# Get user's badges
GET /api/v1/gamification/badges/user
```

### Streaks

Track consecutive days of activity completion.

**Streak Types:**
- `daily_login`: Daily app usage
- `exercise`: Daily workouts
- `meditation`: Daily meditation
- `sleep_quality`: Consistent good sleep
- `healthy_eating`: Daily healthy meals

**Milestone Rewards:**
- 3 days: +50 XP
- 7 days: +100 XP
- 30 days: +300 XP
- 100 days: +1000 XP
- 365 days: +3000 XP

**API Endpoints:**
```bash
# Update streak
POST /api/v1/gamification/streaks/update
{
  "streak_type": "exercise",
  "completed_today": true
}

# Get user streaks
GET /api/v1/gamification/streaks
```

### Daily Challenges

Randomly assigned challenges that refresh daily.

**Difficulty Levels:**
- **Easy**: 25-30 XP (e.g., "Drink water in morning")
- **Medium**: 40-60 XP (e.g., "Walk 8000 steps")
- **Hard**: 60-100 XP (e.g., "Perfect wellness day")

**API Endpoints:**
```bash
# Get today's challenges
GET /api/v1/gamification/challenges/daily

# Accept a challenge
POST /api/v1/gamification/challenges/{challenge_id}/accept

# Complete a challenge
POST /api/v1/gamification/challenges/{challenge_id}/complete
```

### Leaderboards

Compete with others across different time periods.

**Types:**
- XP leaderboard
- Points leaderboard
- Streak leaderboard

**Time Periods:**
- Daily
- Weekly
- Monthly
- All-time

**Privacy:**
- Users can opt-out of leaderboards
- Only visible users are ranked

**API Endpoints:**
```bash
# Get leaderboard
GET /api/v1/gamification/leaderboard?type=xp&period=weekly&limit=100

# Update leaderboard visibility
PUT /api/v1/gamification/leaderboard/visibility
{
  "is_visible": true
}
```

---

## 👥 Social Features

### Friendships

Connect with other users for mutual support.

**Friendship Statuses:**
- `pending`: Friend request sent, awaiting response
- `accepted`: Active friendship
- `blocked`: User blocked

**API Endpoints:**
```bash
# Send friend request
POST /api/v1/social/friends/request
{
  "friend_id": "uuid-here"
}

# Accept friend request
POST /api/v1/social/friends/{friendship_id}/accept

# List friends
GET /api/v1/social/friends

# Remove friend
DELETE /api/v1/social/friends/{friendship_id}
```

### Groups

Create or join communities around shared interests.

**Group Privacy:**
- `public`: Anyone can see and join
- `private`: Visible, but join requires approval
- `secret`: Invite-only, not discoverable

**Group Roles:**
- `admin`: Full control, can delete group
- `moderator`: Manage members and posts
- `member`: Can post and comment

**API Endpoints:**
```bash
# Create group
POST /api/v1/social/groups
{
  "name": "Morning Runners",
  "description": "5 AM running crew",
  "privacy": "public",
  "category": "fitness",
  "max_members": 50
}

# List groups
GET /api/v1/social/groups?category=fitness

# Join group
POST /api/v1/social/groups/{group_id}/join

# Create post
POST /api/v1/social/groups/{group_id}/posts
{
  "content": "Great run this morning!",
  "tags": ["motivation", "fitness"]
}

# Like post
POST /api/v1/social/posts/{post_id}/like

# Comment on post
POST /api/v1/social/posts/{post_id}/comments
{
  "content": "Way to go! 💪"
}
```

### Accountability Partnerships

1-on-1 partnerships for goal accountability.

**Features:**
- Set shared goals
- Regular check-ins
- Progress tracking
- Mutual support

**Check-in Frequencies:**
- Daily
- Weekly
- Bi-weekly

**API Endpoints:**
```bash
# Create partnership
POST /api/v1/social/accountability/create
{
  "partner_id": "uuid-here",
  "check_in_frequency": "daily",
  "goals": [
    {"type": "exercise", "target": "30 min daily"},
    {"type": "meditation", "target": "10 min daily"}
  ]
}

# Log check-in
POST /api/v1/social/accountability/{partnership_id}/check-in
{
  "notes": "Completed workout and meditation today",
  "mood": "energized",
  "progress": {
    "exercise": true,
    "meditation": true
  }
}

# Get partnership details
GET /api/v1/social/accountability/{partnership_id}
```

### Community Challenges

Group challenges with collective or individual goals.

**Goal Types:**
- `individual`: Each participant has their own goal
- `collective`: Group works toward shared goal

**Example Challenges:**
- "Walk 1 million steps together" (collective)
- "30-day meditation challenge" (individual)
- "Fitness February - exercise daily" (individual)

**API Endpoints:**
```bash
# Create challenge
POST /api/v1/social/challenges
{
  "title": "30-Day Meditation Challenge",
  "description": "Meditate every day for 30 days",
  "category": "mindfulness",
  "goal_type": "individual",
  "goal_value": 30,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-03-01T23:59:59Z",
  "is_public": true,
  "rewards": {
    "xp": 500,
    "points": 300,
    "badge_id": 5
  }
}

# Join challenge
POST /api/v1/social/challenges/{challenge_id}/join

# Update progress
POST /api/v1/social/challenges/{challenge_id}/progress
{
  "progress": 15.5,
  "progress_data": {
    "sessions_completed": 15,
    "total_minutes": 180
  }
}
```

---

## 🎤 Voice Interface

Use voice commands to quickly log events.

**Supported Formats:**
- MP3, MP4, WAV, WebM, FLAC, OGG
- Max file size: 25 MB

**Voice Commands:**
- "Log 30 minutes exercise"
- "I meditated for 15 minutes"
- "Slept 8 hours"
- "Had a healthy breakfast"
- "Feeling energized and happy"

**API Endpoint:**
```bash
# Transcribe audio
POST /api/v1/integrations/voice/transcribe
Content-Type: multipart/form-data

file: <audio-file>
language: en

# Execute voice command
POST /api/v1/integrations/voice/command
Content-Type: multipart/form-data

file: <audio-file>
auto_log: true
```

**Response Example:**
```json
{
  "success": true,
  "transcription": "Log 30 minutes exercise cardio",
  "command": {
    "action": "log_event",
    "event_type": "exercise",
    "duration": 30,
    "tags": ["cardio"]
  },
  "life_event_id": "uuid-here"
}
```

---

## 🔗 External Integrations

### Google Calendar

Automatically sync calendar events as life events.

**Setup:**
1. Connect via OAuth 2.0
2. Grant calendar read permissions
3. Auto-sync runs every 6 hours

**Synced Data:**
- Event title and description
- Start/end times
- Location
- Attendees

**API Endpoints:**
```bash
# Start OAuth flow
GET /api/v1/integrations/google_calendar/authorize

# Complete authorization
POST /api/v1/integrations/google_calendar/callback?code=xxx

# Manual sync
POST /api/v1/integrations/{integration_id}/sync

# Disconnect
DELETE /api/v1/integrations/{integration_id}
```

### Fitbit

Sync health and fitness data.

**Synced Metrics:**
- Sleep stages (REM, Deep, Light, Wake)
- Sleep efficiency and quality
- Steps and distance
- Calories burned
- Active minutes
- Heart rate zones
- Body metrics (weight, BMI, body fat %)

**Sync Frequency:** Every 6 hours

**Setup:**
```bash
# Start OAuth
GET /api/v1/integrations/fitbit/authorize

# Complete authorization
POST /api/v1/integrations/fitbit/callback?code=xxx
```

### Oura Ring

Advanced sleep and readiness tracking.

**Synced Metrics:**
- **Sleep Score** (0-100): Overall sleep quality
- **Readiness Score** (0-100): Recovery and preparedness
- **Activity Score** (0-100): Daily movement
- Sleep stages and HRV
- Body temperature deviation
- Respiratory rate
- Workout sessions

**Sync Frequency:** Every 6 hours

**Setup:**
```bash
# Start OAuth
GET /api/v1/integrations/oura/authorize

# Complete authorization
POST /api/v1/integrations/oura/callback?code=xxx
```

### Spotify

Music mood tracking and analysis.

**Synced Data:**
- Recently played tracks (last 50)
- Top tracks and artists
- Audio features (valence, energy, tempo)
- Mood inference from listening patterns

**Mood Quadrant Model:**
- **Happy**: High valence + high energy
- **Calm**: High valence + low energy
- **Tense**: Low valence + high energy
- **Sad**: Low valence + low energy

**Sync Frequency:** Every 6 hours

**Setup:**
```bash
# Start OAuth
GET /api/v1/integrations/spotify/authorize

# Complete authorization
POST /api/v1/integrations/spotify/callback?code=xxx

# View mood analysis
GET /api/v1/integrations/{integration_id}/data?type=mood_analysis
```

### Integration Management

**Common Endpoints:**
```bash
# List user's integrations
GET /api/v1/integrations

# Get integration status
GET /api/v1/integrations/{integration_id}

# Enable/disable sync
PUT /api/v1/integrations/{integration_id}
{
  "sync_enabled": true,
  "sync_frequency": "hourly"
}

# View synced data
GET /api/v1/integrations/{integration_id}/data?limit=50&data_type=sleep_session

# Manual sync
POST /api/v1/integrations/{integration_id}/sync

# Disconnect
DELETE /api/v1/integrations/{integration_id}
```

---

## ⚙️ Background Tasks

### Celery Tasks

**Auto-sync Task:**
Runs hourly to sync all due integrations.

```python
# Celery beat schedule
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'sync-integrations': {
        'task': 'app.tasks.integration_tasks.sync_all_due_integrations',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

**Manual Task Execution:**
```python
from app.tasks.integration_tasks import sync_integration

# Queue sync task
task = sync_integration.delay(integration_id=123)

# Check task status
result = task.get(timeout=60)
```

**Retry Logic:**
- Max retries: 3
- Backoff: Exponential (2^retry * 60 seconds)
- On failure: Error logged to integration

---

## 🔧 Setup & Configuration

### Database Migration

```bash
# Run migration
cd backend
alembic upgrade head

# Seed gamification data
python -m app.db.seed_gamification
```

### Environment Variables

```bash
# .env file additions

# OpenAI (for Whisper voice transcription)
OPENAI_API_KEY=sk-...

# Google Calendar
GOOGLE_CALENDAR_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CALENDAR_CLIENT_SECRET=xxx

# Fitbit
FITBIT_CLIENT_ID=xxx
FITBIT_CLIENT_SECRET=xxx

# Oura
OURA_CLIENT_ID=xxx
OURA_CLIENT_SECRET=xxx

# Spotify
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### OAuth Redirect URIs

Configure these redirect URIs in each provider's developer console:

```
http://localhost:8000/api/v1/integrations/google_calendar/callback
http://localhost:8000/api/v1/integrations/fitbit/callback
http://localhost:8000/api/v1/integrations/oura/callback
http://localhost:8000/api/v1/integrations/spotify/callback
```

### Start Celery Worker

```bash
# Start worker
celery -A app.core.celery_app worker --loglevel=info

# Start beat (scheduler)
celery -A app.core.celery_app beat --loglevel=info

# Start Flower (monitoring)
celery -A app.core.celery_app flower --port=5555
```

### Docker Compose

```yaml
# Already configured in docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: ./backend
    command: celery -A app.core.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres

  celery_beat:
    build: ./backend
    command: celery -A app.core.celery_app beat --loglevel=info
    depends_on:
      - redis
```

---

## 📊 Usage Examples

### Complete Gamification Flow

```python
import httpx

client = httpx.AsyncClient(base_url="http://localhost:8000")
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# 1. Get user stats
stats = await client.get("/api/v1/gamification/stats", headers=headers)
print(f"Level: {stats['level']}, XP: {stats['total_xp']}")

# 2. Update exercise streak
await client.post(
    "/api/v1/gamification/streaks/update",
    json={"streak_type": "exercise", "completed_today": True},
    headers=headers
)

# 3. Get today's challenges
challenges = await client.get(
    "/api/v1/gamification/challenges/daily",
    headers=headers
)

# 4. Complete a challenge
await client.post(
    f"/api/v1/gamification/challenges/{challenges[0]['id']}/complete",
    headers=headers
)

# 5. Check leaderboard rank
leaderboard = await client.get(
    "/api/v1/gamification/leaderboard?type=xp&period=weekly",
    headers=headers
)
```

### Social Interaction Flow

```python
# 1. Create a group
group = await client.post(
    "/api/v1/social/groups",
    json={
        "name": "Morning Meditation",
        "description": "6 AM meditation group",
        "privacy": "public",
        "category": "mindfulness"
    },
    headers=headers
)

# 2. Create a post
post = await client.post(
    f"/api/v1/social/groups/{group['id']}/posts",
    json={
        "content": "Great session this morning! 🧘",
        "tags": ["meditation", "mindfulness"]
    },
    headers=headers
)

# 3. Start accountability partnership
partnership = await client.post(
    "/api/v1/social/accountability/create",
    json={
        "partner_id": "friend-uuid",
        "check_in_frequency": "daily",
        "goals": [{"type": "meditation", "target": "10 min daily"}]
    },
    headers=headers
)
```

### Integration Setup Flow

```python
# 1. Get OAuth URL
auth_url = await client.get(
    "/api/v1/integrations/fitbit/authorize",
    headers=headers
)
print(f"Visit: {auth_url['authorization_url']}")

# 2. After user authorizes, complete OAuth
# (Redirect callback happens automatically)

# 3. Check integration status
integration = await client.get(
    "/api/v1/integrations",
    headers=headers
)
print(f"Fitbit: {integration[0]['sync_status']}")

# 4. View synced sleep data
sleep_data = await client.get(
    f"/api/v1/integrations/{integration[0]['id']}/data?data_type=sleep_session",
    headers=headers
)
```

---

## 🎯 Best Practices

### Gamification
- Award XP immediately after actions for instant gratification
- Use streak multipliers to encourage consistency
- Balance difficulty across daily challenges
- Refresh leaderboards at regular intervals

### Social Features
- Moderate groups actively to maintain quality
- Encourage accountability partnerships for goal achievement
- Use community challenges to drive engagement
- Implement content reporting for safety

### Integrations
- Handle OAuth token refresh transparently
- Respect rate limits (implement backoff)
- Store raw data for reprocessing
- Allow users to control sync frequency

### Background Tasks
- Monitor Celery queue length
- Set appropriate retry limits
- Log failures for debugging
- Use Flower for task monitoring

---

## 🐛 Troubleshooting

### "Integration sync failed"
- Check OAuth token expiration
- Verify provider API credentials
- Review Celery worker logs
- Ensure rate limits not exceeded

### "Achievement not unlocking"
- Verify requirement conditions
- Check achievement is active
- Review progress tracking
- Ensure proper event logging

### "Leaderboard not updating"
- Confirm user opted into leaderboards
- Check leaderboard calculation task
- Verify period dates are correct

### "Voice transcription failed"
- Verify OpenAI API key is set
- Check audio file format/size
- Ensure network connectivity
- Review audio quality

---

## 📈 Monitoring

### Key Metrics
- Daily/Monthly Active Users (DAU/MAU)
- Average user level
- Achievement unlock rate
- Streak retention (7/30/100 days)
- Integration sync success rate
- Daily challenge completion rate
- Social engagement (posts, comments, likes)

### Celery Monitoring
```bash
# Open Flower dashboard
open http://localhost:5555

# Monitor queues
celery -A app.core.celery_app inspect active

# Check failed tasks
celery -A app.core.celery_app events
```

---

## 🚀 Future Enhancements

Potential additions for Phase 9+:

- Push notifications for streak reminders
- Team challenges and tournaments
- Custom achievement creation
- Advanced analytics dashboards
- Mobile app integration
- Wearable device support (Apple Watch, Garmin)
- AI-powered personalized challenges
- Reward redemption system
- Social feed algorithm
- Video/image sharing in groups

---

## 📝 License & Support

For questions, issues, or feature requests, please contact the AURORA_LIFE development team or open an issue on GitHub.

**Documentation Version:** 1.0.0
**Last Updated:** November 27, 2024
**Phase:** 8 - Platform Features
