"""
Database Query Optimization Patterns for AURORA_LIFE

This module provides common query optimization patterns and best practices
to prevent N+1 queries and improve database performance.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from typing import List
from app.models.user import User, OAuthAccount


# ============================================================================
# PATTERN 1: Select Only Required Columns
# ============================================================================
# ❌ BAD: Loading full objects when only IDs are needed
async def get_user_ids_bad(db):
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()
    return [user.id for user in users]  # Loads all columns unnecessarily


# ✅ GOOD: Select only the columns you need
async def get_user_ids_good(db):
    result = await db.execute(
        select(User.id).where(User.is_active == True)
    )
    return result.scalars().all()


# ============================================================================
# PATTERN 2: Eager Loading with selectinload() - For One-to-Many
# ============================================================================
# ❌ BAD: N+1 query problem - accessing relationship in loop
async def get_users_with_oauth_bad(db):
    result = await db.execute(select(User).limit(10))
    users = result.scalars().all()

    # This triggers N additional queries (one per user)
    for user in users:
        for oauth_account in user.oauth_accounts:  # N+1 problem!
            print(oauth_account.provider)


# ✅ GOOD: Use selectinload() to eagerly load relationships
async def get_users_with_oauth_good(db):
    result = await db.execute(
        select(User)
        .options(selectinload(User.oauth_accounts))  # Loads in single query
        .limit(10)
    )
    users = result.scalars().all()

    # No additional queries triggered
    for user in users:
        for oauth_account in user.oauth_accounts:
            print(oauth_account.provider)


# ============================================================================
# PATTERN 3: Eager Loading with joinedload() - For Many-to-One
# ============================================================================
# ❌ BAD: N+1 when accessing parent relationship
async def get_oauth_accounts_bad(db):
    result = await db.execute(select(OAuthAccount).limit(10))
    accounts = result.scalars().all()

    # Triggers N queries to load each user
    for account in accounts:
        print(account.user.email)  # N+1 problem!


# ✅ GOOD: Use joinedload() for many-to-one relationships
async def get_oauth_accounts_good(db):
    result = await db.execute(
        select(OAuthAccount)
        .options(joinedload(OAuthAccount.user))  # LEFT OUTER JOIN
        .limit(10)
    )
    accounts = result.scalars().unique().all()  # unique() removes JOIN duplicates

    for account in accounts:
        print(account.user.email)  # No additional queries


# ============================================================================
# PATTERN 4: Combining Filters with Joins using contains_eager()
# ============================================================================
# ✅ GOOD: Filter on joined table and eagerly load relationship
async def get_users_with_google_oauth(db):
    result = await db.execute(
        select(User)
        .join(User.oauth_accounts)
        .where(OAuthAccount.provider == "google")
        .options(contains_eager(User.oauth_accounts))  # Reuse JOIN for eager loading
    )
    return result.scalars().unique().all()


# ============================================================================
# PATTERN 5: Nested Eager Loading
# ============================================================================
# If you have User -> Posts -> Comments, load all at once:
# result = await db.execute(
#     select(User)
#     .options(
#         selectinload(User.posts)
#         .selectinload(Post.comments)
#     )
# )


# ============================================================================
# PATTERN 6: Counting Without Loading Objects
# ============================================================================
from sqlalchemy import func

# ❌ BAD: Loads all objects just to count
async def count_users_bad(db):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return len(users)


# ✅ GOOD: Count directly in database
async def count_users_good(db):
    result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    return result.scalar()


# ============================================================================
# PATTERN 7: Batch Loading by IDs
# ============================================================================
# ❌ BAD: Multiple separate queries
async def get_users_by_ids_bad(db, user_ids: List[int]):
    users = []
    for user_id in user_ids:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            users.append(user)
    return users


# ✅ GOOD: Single query with IN clause
async def get_users_by_ids_good(db, user_ids: List[int]):
    result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    return result.scalars().all()


# ============================================================================
# INDEXING RECOMMENDATIONS
# ============================================================================
"""
Common indexes to add for AURORA_LIFE:

1. User model:
   - CREATE INDEX idx_users_email ON users(email);  # Already unique
   - CREATE INDEX idx_users_is_active ON users(is_active);
   - CREATE INDEX idx_users_role ON users(role);

2. OAuthAccount model:
   - CREATE INDEX idx_oauth_provider_user_id ON oauth_accounts(provider, provider_user_id);
   - CREATE INDEX idx_oauth_user_id ON oauth_accounts(user_id);  # Foreign key

3. LifeEvent model:
   - CREATE INDEX idx_life_events_user_time ON life_events(user_id, event_time DESC);
   - CREATE INDEX idx_life_events_type ON life_events(event_type);
   - CREATE INDEX idx_life_events_category ON life_events(event_category);

Add these in Alembic migrations:
```python
# Example migration
def upgrade():
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_life_events_user_time', 'life_events', ['user_id', 'event_time'])
```
"""


# ============================================================================
# QUERY PERFORMANCE CHECKLIST
# ============================================================================
"""
Before deploying a query to production, check:

✅ 1. Are you loading full objects when only specific columns are needed?
   → Use select(Model.column1, Model.column2) instead

✅ 2. Are you accessing relationships inside loops?
   → Add .options(selectinload(Model.relationship))

✅ 3. Are you filtering on joined tables?
   → Use .join() with .options(contains_eager())

✅ 4. Are you counting results?
   → Use select(func.count()) instead of len()

✅ 5. Are you loading objects by IDs in a loop?
   → Use .where(Model.id.in_(ids)) for batch loading

✅ 6. Do your WHERE clauses use indexed columns?
   → Add indexes for frequently queried columns

✅ 7. Are you using LIMIT/OFFSET for pagination?
   → For large datasets, consider cursor-based pagination

✅ 8. Are you using bulk operations?
   → Use bulk_insert_mappings() or bulk_update_mappings() for many rows
"""
