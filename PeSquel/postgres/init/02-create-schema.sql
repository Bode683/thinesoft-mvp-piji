-- 02-create-schema.sql
-- Create API schema for PostgREST
-- Includes sample todos table with RLS policies

-- Create api schema
CREATE SCHEMA IF NOT EXISTS api;

-- Grant usage on api schema
GRANT USAGE ON SCHEMA api TO PUBLIC;

-- Create a sample table for testing
CREATE TABLE IF NOT EXISTS api.todos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION api.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to todos table
CREATE TRIGGER update_todos_updated_at
BEFORE UPDATE ON api.todos
FOR EACH ROW
EXECUTE FUNCTION api.update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE api.todos ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for api_anon role (allow all for MVP testing)
CREATE POLICY "Allow anonymous read access" ON api.todos
  FOR SELECT
  TO api_anon
  USING (true);

CREATE POLICY "Allow anonymous insert access" ON api.todos
  FOR INSERT
  TO api_anon
  WITH CHECK (true);

CREATE POLICY "Allow anonymous update access" ON api.todos
  FOR UPDATE
  TO api_anon
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow anonymous delete access" ON api.todos
  FOR DELETE
  TO api_anon
  USING (true);

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON api.todos TO api_anon;
