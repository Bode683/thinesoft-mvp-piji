-- Enable pgAudit extension
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Create a test table for verification
CREATE TABLE IF NOT EXISTS audit_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert test data to generate audit logs
INSERT INTO audit_test (name) VALUES ('Test Record 1');
INSERT INTO audit_test (name) VALUES ('Test Record 2');

-- Grant permissions on test table
GRANT SELECT ON audit_test TO app_reader;
GRANT ALL ON audit_test TO app_writer;
GRANT USAGE ON SEQUENCE audit_test_id_seq TO app_writer;
