-- 04-create-keycloak-db.sql
-- Create dedicated database for Keycloak authentication service
-- Part of QueWall microservice integration

-- Create keycloak database
CREATE DATABASE keycloak
  WITH
  OWNER = postgres
  ENCODING = 'UTF8'
  LC_COLLATE = 'en_US.utf8'
  LC_CTYPE = 'en_US.utf8'
  TABLESPACE = pg_default
  CONNECTION LIMIT = -1;

-- Create keycloak user with password from environment
DO $$
DECLARE
  keycloak_password TEXT;
BEGIN
  -- Get password from environment variable set by custom entrypoint
  keycloak_password := current_setting('env.KEYCLOAK_DB_PASSWORD', true);

  IF keycloak_password IS NULL THEN
    RAISE EXCEPTION 'KEYCLOAK_DB_PASSWORD environment variable not set';
  END IF;

  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keycloak') THEN
    EXECUTE format('CREATE USER keycloak WITH PASSWORD %L', keycloak_password);
  END IF;
END $$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;

-- Log creation
DO $$
BEGIN
  RAISE NOTICE 'Keycloak database and user created at %', NOW();
END $$;
