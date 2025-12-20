-- 03-create-roles.sql
-- Create database roles for PostgREST
-- Defines roles and permissions for the API

-- Create anonymous role (for unauthenticated requests)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_anon') THEN
    CREATE ROLE api_anon NOLOGIN;
  END IF;
END $$;

-- Create authenticator role (for pgBouncer connection)
-- Password is read from AUTHENTICATOR_PASSWORD environment variable
-- which is set by the custom PostgreSQL entrypoint
DO $$
DECLARE
  auth_password TEXT;
BEGIN
  -- Get password from environment variable set by custom entrypoint
  auth_password := current_setting('env.AUTHENTICATOR_PASSWORD', true);

  IF auth_password IS NULL THEN
    RAISE EXCEPTION 'AUTHENTICATOR_PASSWORD environment variable not set';
  END IF;

  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
    EXECUTE format('CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD %L', auth_password);
  END IF;
END $$;

-- Grant necessary permissions
GRANT api_anon TO authenticator;
GRANT USAGE ON SCHEMA api TO api_anon;
GRANT ALL ON ALL TABLES IN SCHEMA api TO api_anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA api TO api_anon;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA api TO api_anon;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA api
  GRANT ALL ON TABLES TO api_anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
  GRANT ALL ON SEQUENCES TO api_anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
  GRANT ALL ON FUNCTIONS TO api_anon;

-- Log role creation
DO $$
BEGIN
  RAISE NOTICE 'Database roles created successfully at %', NOW();
END $$;
