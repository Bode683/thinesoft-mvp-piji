-- 01-init-db.sql
-- Initial database setup for PeSequel
-- Creates extensions and sets basic configuration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
  RAISE NOTICE 'PeSequel database initialized at %', NOW();
END $$;
