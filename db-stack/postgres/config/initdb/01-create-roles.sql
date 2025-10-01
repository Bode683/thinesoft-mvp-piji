-- Create application roles and users
CREATE ROLE app_reader;
CREATE ROLE app_writer;

-- Create application user
CREATE USER app_user WITH PASSWORD 'password';

-- Grant roles to app_user
GRANT app_reader TO app_user;
GRANT app_writer TO app_user;

-- Grant basic permissions
GRANT CONNECT ON DATABASE postgres TO app_reader;
GRANT USAGE ON SCHEMA public TO app_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO app_reader;

GRANT CONNECT ON DATABASE postgres TO app_writer;
GRANT USAGE ON SCHEMA public TO app_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_writer;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO app_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_writer;

-- Create auditor role (optional, for reviewing audit logs)
CREATE ROLE pgauditor;
GRANT pg_read_all_settings TO pgauditor;
GRANT pg_read_all_stats TO pgauditor;
