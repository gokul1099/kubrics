-- PostgreSQL initialization script with pgvector support
-- This script runs automatically when the container is first created

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Create a sample embeddings table (you can modify this as needed)
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- Adjust dimension based on your embedding model
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for vector similarity search (using cosine distance)
CREATE INDEX IF NOT EXISTS embeddings_embedding_idx ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Grant permissions (if using a different user than postgres)
-- Uncomment and modify if you have a different application user
-- GRANT ALL PRIVILEGES ON TABLE embeddings TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE embeddings_id_seq TO your_app_user;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL with pgvector initialized successfully!';
    RAISE NOTICE 'pgvector extension is enabled and ready to use.';
END $$;
