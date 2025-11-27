-- AURORA LIFE - Database Initialization Script
-- This script runs automatically when the database container first starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For GIN indexes on multiple columns

-- Create database (if not exists)
SELECT 'CREATE DATABASE aurora_life'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aurora_life')\gexec

-- Connect to the database
\c aurora_life

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE aurora_life TO aurora;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aurora;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aurora;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aurora;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aurora;

-- Print success message
SELECT 'Database initialized successfully!' AS status;
