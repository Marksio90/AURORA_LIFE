"""Initial schema with optimized indexes

Revision ID: 001
Revises:
Create Date: 2024-01-16 10:00:00.000000

This migration creates the initial database schema for AURORA_LIFE with:
- All core tables (users, events, predictions, insights, etc.)
- Optimized indexes for common queries
- Foreign key constraints
- Check constraints
- Triggers for updated_at timestamps
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200)),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('role', sa.String(50), default='user', nullable=False),
        sa.Column('preferences', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes for users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_role', 'users', ['role'])

    # Events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), default={}),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Composite indexes for events (most common queries)
    op.create_index('idx_events_user_time', 'events', ['user_id', 'event_time'])
    op.create_index('idx_events_user_type_time', 'events', ['user_id', 'event_type', 'event_time'])
    op.create_index('idx_events_type', 'events', ['event_type'])
    op.create_index('idx_events_event_time', 'events', ['event_time'])

    # GIN index for JSONB data and array tags
    op.create_index('idx_events_event_data_gin', 'events', ['event_data'], postgresql_using='gin')
    op.create_index('idx_events_tags_gin', 'events', ['tags'], postgresql_using='gin')

    # Predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),  # 'energy' or 'mood'
        sa.Column('prediction', sa.Float()),
        sa.Column('prediction_class', sa.String(50)),  # For mood classification
        sa.Column('confidence', sa.Float()),
        sa.Column('class_probabilities', postgresql.JSONB()),
        sa.Column('features_used', postgresql.JSONB()),
        sa.Column('model_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for predictions
    op.create_index('idx_predictions_user_created', 'predictions', ['user_id', 'created_at'])
    op.create_index('idx_predictions_user_model', 'predictions', ['user_id', 'model_type', 'created_at'])

    # Insights table
    op.create_table(
        'insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('insight_type', sa.String(50)),  # 'pattern', 'recommendation', 'alert'
        sa.Column('context', sa.String(100)),  # 'health', 'productivity', etc.
        sa.Column('confidence', sa.Float()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for insights
    op.create_index('idx_insights_user_created', 'insights', ['user_id', 'created_at'])
    op.create_index('idx_insights_user_read', 'insights', ['user_id', 'is_read'])
    op.create_index('idx_insights_type', 'insights', ['insight_type'])

    # Timeline aggregations table (for performance)
    op.create_table(
        'timeline_aggregations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('event_counts', postgresql.JSONB(), default={}),  # {event_type: count}
        sa.Column('metrics', postgresql.JSONB(), default={}),  # {metric: value}
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'date', name='uq_timeline_user_date')
    )

    # Indexes for timeline aggregations
    op.create_index('idx_timeline_user_date', 'timeline_aggregations', ['user_id', 'date'])

    # Verification tokens table
    op.create_table(
        'verification_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('token_type', sa.String(50), nullable=False),  # 'email_verification', 'password_reset'
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for verification tokens
    op.create_index('idx_verification_tokens_token', 'verification_tokens', ['token'])
    op.create_index('idx_verification_tokens_user', 'verification_tokens', ['user_id', 'token_type'])

    # Webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String), default=[]),  # ['event.created', 'prediction.generated']
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for webhooks
    op.create_index('idx_webhooks_user_active', 'webhooks', ['user_id', 'is_active'])

    # Webhook deliveries table (for tracking)
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), default={}),
        sa.Column('response_status', sa.Integer()),
        sa.Column('response_body', sa.Text()),
        sa.Column('attempt_count', sa.Integer(), default=1),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE'),
    )

    # Indexes for webhook deliveries
    op.create_index('idx_webhook_deliveries_webhook', 'webhook_deliveries', ['webhook_id', 'created_at'])
    op.create_index('idx_webhook_deliveries_status', 'webhook_deliveries', ['response_status'])

    # Audit log table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('changes', postgresql.JSONB(), default={}),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes for audit logs
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])

    # Partitioning for audit_logs (by month)
    # Note: This would require PostgreSQL 10+ and additional setup
    # Commented out for initial migration, can be enabled later
    # op.execute("""
    #     CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
    #     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    # """)

    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Add updated_at triggers to relevant tables
    for table in ['users', 'events', 'timeline_aggregations', 'webhooks']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create function for timeline aggregation
    op.execute("""
        CREATE OR REPLACE FUNCTION update_timeline_aggregation()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO timeline_aggregations (id, user_id, date, event_counts)
            VALUES (
                gen_random_uuid(),
                NEW.user_id,
                DATE(NEW.event_time),
                jsonb_build_object(NEW.event_type, 1)
            )
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                event_counts = timeline_aggregations.event_counts ||
                               jsonb_build_object(
                                   NEW.event_type,
                                   COALESCE((timeline_aggregations.event_counts->NEW.event_type)::int, 0) + 1
                               ),
                updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Add trigger for timeline aggregation on event insert
    op.execute("""
        CREATE TRIGGER update_timeline_on_event_insert
        AFTER INSERT ON events
        FOR EACH ROW
        EXECUTE FUNCTION update_timeline_aggregation();
    """)


def downgrade():
    # Drop triggers
    for table in ['users', 'events', 'timeline_aggregations', 'webhooks']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")

    op.execute("DROP TRIGGER IF EXISTS update_timeline_on_event_insert ON events;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.execute("DROP FUNCTION IF EXISTS update_timeline_aggregation();")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('audit_logs')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
    op.drop_table('verification_tokens')
    op.drop_table('timeline_aggregations')
    op.drop_table('insights')
    op.drop_table('predictions')
    op.drop_table('events')
    op.drop_table('users')
