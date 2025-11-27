"""
Seed data for gamification system (achievements, badges, daily challenges)

Run with: python -m app.db.seed_gamification
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.gamification import Achievement, Badge, DailyChallenge
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== ACHIEVEMENT DEFINITIONS ====================

ACHIEVEMENTS = [
    # ===== HEALTH CATEGORY =====
    {
        "name": "Early Bird",
        "description": "Wake up before 6 AM for 7 consecutive days",
        "category": "health",
        "icon": "sunrise",
        "points": 150,
        "xp_reward": 100,
        "rarity": "common",
        "requirements": {
            "type": "consecutive_days",
            "metric": "wake_time",
            "days": 7,
            "condition": "before",
            "value": "06:00"
        }
    },
    {
        "name": "Sleep Champion",
        "description": "Get 8+ hours of quality sleep for 30 days",
        "category": "health",
        "icon": "bed",
        "points": 500,
        "xp_reward": 300,
        "rarity": "rare",
        "requirements": {
            "type": "consecutive_days",
            "metric": "sleep_duration",
            "days": 30,
            "condition": ">=",
            "value": 8.0
        }
    },
    {
        "name": "Hydration Hero",
        "description": "Log 8+ glasses of water daily for 14 days",
        "category": "health",
        "icon": "water",
        "points": 200,
        "xp_reward": 150,
        "rarity": "common",
        "requirements": {
            "type": "consecutive_days",
            "metric": "water_intake",
            "days": 14,
            "condition": ">=",
            "value": 8
        }
    },
    {
        "name": "Fitness Fanatic",
        "description": "Complete 100 workout sessions",
        "category": "health",
        "icon": "dumbbell",
        "points": 1000,
        "xp_reward": 500,
        "rarity": "epic",
        "requirements": {
            "type": "total_count",
            "metric": "exercise_sessions",
            "value": 100
        }
    },
    {
        "name": "Mindful Master",
        "description": "Complete 50 meditation sessions",
        "category": "health",
        "icon": "lotus",
        "points": 600,
        "xp_reward": 400,
        "rarity": "rare",
        "requirements": {
            "type": "total_count",
            "metric": "meditation_sessions",
            "value": 50
        }
    },
    {
        "name": "Step Master",
        "description": "Walk 10,000+ steps for 30 consecutive days",
        "category": "health",
        "icon": "footprints",
        "points": 800,
        "xp_reward": 450,
        "rarity": "epic",
        "requirements": {
            "type": "consecutive_days",
            "metric": "steps",
            "days": 30,
            "condition": ">=",
            "value": 10000
        }
    },
    {
        "name": "Nutrition Ninja",
        "description": "Log all meals for 21 consecutive days",
        "category": "health",
        "icon": "apple",
        "points": 400,
        "xp_reward": 250,
        "rarity": "rare",
        "requirements": {
            "type": "consecutive_days",
            "metric": "meals_logged",
            "days": 21,
            "condition": ">=",
            "value": 3
        }
    },

    # ===== CONSISTENCY CATEGORY =====
    {
        "name": "Week Warrior",
        "description": "Log in for 7 consecutive days",
        "category": "consistency",
        "icon": "calendar-check",
        "points": 100,
        "xp_reward": 75,
        "rarity": "common",
        "requirements": {
            "type": "streak",
            "metric": "daily_login",
            "days": 7
        }
    },
    {
        "name": "Monthly Master",
        "description": "Log in for 30 consecutive days",
        "category": "consistency",
        "icon": "calendar-star",
        "points": 500,
        "xp_reward": 350,
        "rarity": "rare",
        "requirements": {
            "type": "streak",
            "metric": "daily_login",
            "days": 30
        }
    },
    {
        "name": "Century Streak",
        "description": "Maintain a 100-day login streak",
        "category": "consistency",
        "icon": "fire",
        "points": 2000,
        "xp_reward": 1000,
        "rarity": "legendary",
        "requirements": {
            "type": "streak",
            "metric": "daily_login",
            "days": 100
        }
    },
    {
        "name": "Yearly Devotion",
        "description": "Log in for 365 consecutive days",
        "category": "consistency",
        "icon": "crown",
        "points": 5000,
        "xp_reward": 3000,
        "rarity": "legendary",
        "requirements": {
            "type": "streak",
            "metric": "daily_login",
            "days": 365
        }
    },
    {
        "name": "Perfect Week",
        "description": "Complete all daily challenges for 7 days straight",
        "category": "consistency",
        "icon": "star",
        "points": 300,
        "xp_reward": 200,
        "rarity": "rare",
        "requirements": {
            "type": "consecutive_days",
            "metric": "daily_challenges_completed",
            "days": 7,
            "condition": "all"
        }
    },

    # ===== SOCIAL CATEGORY =====
    {
        "name": "Social Butterfly",
        "description": "Make 10 friends",
        "category": "social",
        "icon": "users",
        "points": 200,
        "xp_reward": 150,
        "rarity": "common",
        "requirements": {
            "type": "total_count",
            "metric": "friends",
            "value": 10
        }
    },
    {
        "name": "Community Leader",
        "description": "Create and maintain a group with 50+ members",
        "category": "social",
        "icon": "user-crown",
        "points": 1000,
        "xp_reward": 600,
        "rarity": "epic",
        "requirements": {
            "type": "group_members",
            "metric": "created_group",
            "value": 50
        }
    },
    {
        "name": "Challenge Champion",
        "description": "Complete 20 community challenges",
        "category": "social",
        "icon": "trophy",
        "points": 800,
        "xp_reward": 500,
        "rarity": "epic",
        "requirements": {
            "type": "total_count",
            "metric": "community_challenges_completed",
            "value": 20
        }
    },
    {
        "name": "Accountability Partner",
        "description": "Maintain an active accountability partnership for 30 days",
        "category": "social",
        "icon": "handshake",
        "points": 400,
        "xp_reward": 250,
        "rarity": "rare",
        "requirements": {
            "type": "partnership_duration",
            "metric": "accountability_partnership",
            "days": 30
        }
    },
    {
        "name": "Motivator",
        "description": "Receive 100 likes on your posts",
        "category": "social",
        "icon": "heart",
        "points": 300,
        "xp_reward": 200,
        "rarity": "rare",
        "requirements": {
            "type": "total_count",
            "metric": "post_likes_received",
            "value": 100
        }
    },

    # ===== MILESTONE CATEGORY =====
    {
        "name": "Getting Started",
        "description": "Complete your first life event log",
        "category": "milestone",
        "icon": "flag",
        "points": 50,
        "xp_reward": 25,
        "rarity": "common",
        "requirements": {
            "type": "total_count",
            "metric": "life_events_logged",
            "value": 1
        }
    },
    {
        "name": "Century Logger",
        "description": "Log 100 life events",
        "category": "milestone",
        "icon": "book",
        "points": 500,
        "xp_reward": 300,
        "rarity": "rare",
        "requirements": {
            "type": "total_count",
            "metric": "life_events_logged",
            "value": 100
        }
    },
    {
        "name": "Level 10",
        "description": "Reach level 10",
        "category": "milestone",
        "icon": "level-up",
        "points": 500,
        "xp_reward": 0,  # Already earned XP to reach level
        "rarity": "rare",
        "requirements": {
            "type": "level",
            "metric": "user_level",
            "value": 10
        }
    },
    {
        "name": "Level 25",
        "description": "Reach level 25",
        "category": "milestone",
        "icon": "level-up",
        "points": 1500,
        "xp_reward": 0,
        "rarity": "epic",
        "requirements": {
            "type": "level",
            "metric": "user_level",
            "value": 25
        }
    },
    {
        "name": "Level 50",
        "description": "Reach level 50",
        "category": "milestone",
        "icon": "level-up",
        "points": 5000,
        "xp_reward": 0,
        "rarity": "legendary",
        "requirements": {
            "type": "level",
            "metric": "user_level",
            "value": 50
        }
    },
    {
        "name": "XP Master",
        "description": "Earn 10,000 total XP",
        "category": "milestone",
        "icon": "gem",
        "points": 2000,
        "xp_reward": 500,
        "rarity": "epic",
        "requirements": {
            "type": "total_value",
            "metric": "total_xp",
            "value": 10000
        }
    },
    {
        "name": "First Integration",
        "description": "Connect your first external integration",
        "category": "milestone",
        "icon": "plug",
        "points": 100,
        "xp_reward": 75,
        "rarity": "common",
        "requirements": {
            "type": "total_count",
            "metric": "integrations_connected",
            "value": 1
        }
    },
    {
        "name": "Data Enthusiast",
        "description": "Sync data from 5 different integrations",
        "category": "milestone",
        "icon": "database",
        "points": 600,
        "xp_reward": 400,
        "rarity": "epic",
        "requirements": {
            "type": "total_count",
            "metric": "integrations_connected",
            "value": 5
        }
    },
]


# ==================== BADGE DEFINITIONS ====================

BADGES = [
    {
        "name": "Founder",
        "description": "One of the first 1000 users to join AURORA_LIFE",
        "icon": "crown",
        "color": "#FFD700",  # Gold
        "requirements": {
            "type": "user_id_range",
            "max_user_id": 1000
        }
    },
    {
        "name": "Beta Tester",
        "description": "Participated in the beta testing phase",
        "icon": "flask",
        "color": "#9B59B6",  # Purple
        "requirements": {
            "type": "manual",
            "note": "Manually awarded to beta testers"
        }
    },
    {
        "name": "Sleep Expert",
        "description": "Maintained excellent sleep habits for 90 days",
        "icon": "moon",
        "color": "#3498DB",  # Blue
        "requirements": {
            "type": "consecutive_days",
            "metric": "sleep_quality",
            "days": 90,
            "condition": ">=",
            "value": 8.0
        }
    },
    {
        "name": "Fitness Legend",
        "description": "Completed 500 workout sessions",
        "icon": "muscle",
        "color": "#E74C3C",  # Red
        "requirements": {
            "type": "total_count",
            "metric": "exercise_sessions",
            "value": 500
        }
    },
    {
        "name": "Zen Master",
        "description": "Completed 365 meditation sessions",
        "icon": "om",
        "color": "#1ABC9C",  # Teal
        "requirements": {
            "type": "total_count",
            "metric": "meditation_sessions",
            "value": 365
        }
    },
    {
        "name": "Social Star",
        "description": "Have 100+ friends and 500+ post likes",
        "icon": "star",
        "color": "#F39C12",  # Orange
        "requirements": {
            "type": "composite",
            "conditions": [
                {"metric": "friends", "value": 100},
                {"metric": "post_likes_received", "value": 500}
            ]
        }
    },
    {
        "name": "Streak Legend",
        "description": "Maintain a 365-day login streak",
        "icon": "fire",
        "color": "#E67E22",  # Dark orange
        "requirements": {
            "type": "streak",
            "metric": "daily_login",
            "days": 365
        }
    },
    {
        "name": "Max Level",
        "description": "Reached level 100",
        "icon": "diamond",
        "color": "#95A5A6",  # Silver
        "requirements": {
            "type": "level",
            "metric": "user_level",
            "value": 100
        }
    },
    {
        "name": "Champion",
        "description": "Rank #1 on the all-time leaderboard",
        "icon": "trophy",
        "color": "#FFD700",  # Gold
        "requirements": {
            "type": "leaderboard_rank",
            "leaderboard_type": "xp",
            "time_period": "all_time",
            "rank": 1
        }
    },
    {
        "name": "Integration Master",
        "description": "Connected and actively using 10+ integrations",
        "icon": "link",
        "color": "#34495E",  # Dark blue-gray
        "requirements": {
            "type": "total_count",
            "metric": "active_integrations",
            "value": 10
        }
    },
]


# ==================== DAILY CHALLENGE TEMPLATES ====================

DAILY_CHALLENGE_TEMPLATES = [
    # Easy challenges
    {
        "title": "Morning Hydration",
        "description": "Drink a glass of water within 30 minutes of waking up",
        "category": "health",
        "difficulty": "easy",
        "xp_reward": 25,
        "points_reward": 10,
        "requirements": {
            "type": "log_event",
            "metric": "water_intake",
            "value": 1,
            "timeframe": "morning"
        }
    },
    {
        "title": "5-Minute Meditation",
        "description": "Complete a 5-minute meditation session",
        "category": "mindfulness",
        "difficulty": "easy",
        "xp_reward": 30,
        "points_reward": 15,
        "requirements": {
            "type": "log_event",
            "metric": "meditation",
            "duration_min": 5
        }
    },
    {
        "title": "Gratitude Journal",
        "description": "Write down 3 things you're grateful for today",
        "category": "mindfulness",
        "difficulty": "easy",
        "xp_reward": 25,
        "points_reward": 10,
        "requirements": {
            "type": "log_event",
            "metric": "gratitude_journal",
            "value": 3
        }
    },
    {
        "title": "Quick Walk",
        "description": "Take a 10-minute walk",
        "category": "fitness",
        "difficulty": "easy",
        "xp_reward": 30,
        "points_reward": 15,
        "requirements": {
            "type": "log_event",
            "metric": "walk",
            "duration_min": 10
        }
    },

    # Medium challenges
    {
        "title": "Step Challenge",
        "description": "Walk 8,000 steps today",
        "category": "fitness",
        "difficulty": "medium",
        "xp_reward": 50,
        "points_reward": 25,
        "requirements": {
            "type": "daily_metric",
            "metric": "steps",
            "value": 8000
        }
    },
    {
        "title": "Healthy Eating",
        "description": "Log 3 healthy meals and avoid junk food",
        "category": "nutrition",
        "difficulty": "medium",
        "xp_reward": 50,
        "points_reward": 25,
        "requirements": {
            "type": "log_event",
            "metric": "healthy_meals",
            "value": 3
        }
    },
    {
        "title": "Screen-Free Hour",
        "description": "Spend 1 hour without screens before bed",
        "category": "wellness",
        "difficulty": "medium",
        "xp_reward": 40,
        "points_reward": 20,
        "requirements": {
            "type": "log_event",
            "metric": "screen_free_time",
            "duration_min": 60,
            "timeframe": "evening"
        }
    },
    {
        "title": "Workout Session",
        "description": "Complete a 30-minute workout",
        "category": "fitness",
        "difficulty": "medium",
        "xp_reward": 60,
        "points_reward": 30,
        "requirements": {
            "type": "log_event",
            "metric": "exercise",
            "duration_min": 30
        }
    },

    # Hard challenges
    {
        "title": "Perfect Day",
        "description": "Exercise, meditate, eat healthy, and get 8+ hours sleep",
        "category": "wellness",
        "difficulty": "hard",
        "xp_reward": 100,
        "points_reward": 50,
        "requirements": {
            "type": "composite",
            "conditions": [
                {"metric": "exercise", "duration_min": 30},
                {"metric": "meditation", "duration_min": 10},
                {"metric": "healthy_meals", "value": 3},
                {"metric": "sleep_duration", "value": 8}
            ]
        }
    },
    {
        "title": "10K Steps",
        "description": "Walk 10,000 steps today",
        "category": "fitness",
        "difficulty": "hard",
        "xp_reward": 75,
        "points_reward": 40,
        "requirements": {
            "type": "daily_metric",
            "metric": "steps",
            "value": 10000
        }
    },
    {
        "title": "Social Connection",
        "description": "Have a meaningful conversation with a friend or family member for 30+ minutes",
        "category": "social",
        "difficulty": "hard",
        "xp_reward": 60,
        "points_reward": 30,
        "requirements": {
            "type": "log_event",
            "metric": "social_interaction",
            "duration_min": 30
        }
    },
]


# ==================== SEED FUNCTIONS ====================

async def seed_achievements(db: AsyncSession) -> int:
    """Seed achievement definitions"""
    count = 0
    for ach_data in ACHIEVEMENTS:
        achievement = Achievement(**ach_data)
        db.add(achievement)
        count += 1

    await db.commit()
    logger.info(f"✅ Seeded {count} achievements")
    return count


async def seed_badges(db: AsyncSession) -> int:
    """Seed badge definitions"""
    count = 0
    for badge_data in BADGES:
        badge = Badge(**badge_data)
        db.add(badge)
        count += 1

    await db.commit()
    logger.info(f"✅ Seeded {count} badges")
    return count


async def seed_daily_challenges(db: AsyncSession) -> int:
    """Seed daily challenge templates"""
    # Note: These are templates. Actual daily challenges should be
    # created by a scheduler that picks random challenges for each day
    logger.info(f"📝 {len(DAILY_CHALLENGE_TEMPLATES)} daily challenge templates available")
    logger.info("   (Use gamification service to generate actual daily challenges)")
    return len(DAILY_CHALLENGE_TEMPLATES)


async def main():
    """Run all seed operations"""
    logger.info("🌱 Starting gamification seed data...")

    async with AsyncSessionLocal() as db:
        try:
            # Seed achievements
            ach_count = await seed_achievements(db)

            # Seed badges
            badge_count = await seed_badges(db)

            # Log challenge templates
            challenge_count = await seed_daily_challenges(db)

            logger.info(f"\n✨ Gamification seed complete!")
            logger.info(f"   - {ach_count} achievements")
            logger.info(f"   - {badge_count} badges")
            logger.info(f"   - {challenge_count} challenge templates")

        except Exception as e:
            logger.error(f"❌ Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
